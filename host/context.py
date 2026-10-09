"""Convert Binary Ninja objects into bounded provider-neutral context."""

import os
from collections.abc import Iterable, Iterator
from itertools import chain
from typing import Any, Optional

from binaryninja import BinaryView, Function

from ..core.models import (
    ContextBundle,
    ContextItem,
    ContextOptions,
    FunctionContext,
    ProviderCancelled,
    ProviderError,
)
from ..core.policy import build_context_bundle, truncate_text
from ..core.provider import CancelCheck

MAX_REFERENCE_STEPS = 4096
MAX_HLIL_INSTRUCTIONS = 100_000


class _TraversalBudget:
    def __init__(self, limit: int = MAX_REFERENCE_STEPS):
        self.remaining = limit
        self.exhausted = False

    def step(self, is_cancelled: CancelCheck) -> bool:
        _check_cancelled(is_cancelled)
        if self.remaining <= 0:
            self.exhausted = True
            return False
        self.remaining -= 1
        return True


def _check_cancelled(is_cancelled: CancelCheck) -> None:
    if is_cancelled is not None and is_cancelled():
        raise ProviderCancelled("Context collection cancelled.")


def _hlil_lines(
    function: Function,
    is_cancelled: CancelCheck = None,
    selection: Optional[tuple[int, int]] = None,
    budget: Optional[_TraversalBudget] = None,
) -> Iterator[str]:
    _check_cancelled(is_cancelled)
    hlil = function.hlil
    if hlil is None:
        raise ProviderError(
            f"Binary Ninja could not produce HLIL for {function.name}."
        )
    budget = budget if budget is not None else _TraversalBudget(MAX_HLIL_INSTRUCTIONS)
    for instruction in hlil.instructions:
        if not budget.step(is_cancelled):
            return
        address = instruction.address
        if selection is None or selection[0] <= address < selection[1]:
            yield f"0x{address:x}: {instruction}"


def _bounded_text(
    lines: Iterable[str],
    limit: int,
    marker: str,
    is_cancelled: CancelCheck = None,
) -> tuple[str, bool]:
    """Keep only a budget-sized prefix plus one character proving overflow."""
    if limit < 1:
        raise ValueError("max_context_chars must be positive")
    parts: list[str] = []
    length = 0
    for line in lines:
        _check_cancelled(is_cancelled)
        separator = "\n" if parts else ""
        available = limit + 1 - length
        piece = (separator + line)[:available]
        parts.append(piece)
        length += len(piece)
        if length > limit:
            break
    return truncate_text("".join(parts), limit, marker)


def _mark_truncated(text: str, limit: int, marker: str) -> tuple[str, bool]:
    if limit <= len(marker):
        return marker[:limit], True
    return text[:limit - len(marker)].rstrip() + marker, True


def _bounded_hlil(
    function: Function,
    limit: int,
    marker: str,
    is_cancelled: CancelCheck,
    selection: Optional[tuple[int, int]] = None,
) -> tuple[str, bool]:
    budget = _TraversalBudget(MAX_HLIL_INSTRUCTIONS)
    text, truncated = _bounded_text(
        _hlil_lines(function, is_cancelled, selection, budget), limit, marker, is_cancelled,
    )
    if budget.exhausted:
        return _mark_truncated(text, limit, marker)
    return text, truncated


def _function_item(
    function: Function,
    kind: str,
    label: str,
    item_limit: int,
    is_cancelled: CancelCheck = None,
) -> ContextItem:
    rendered, truncated = _bounded_hlil(
        function,
        item_limit,
        f"\n\n[{label} truncated by Axio Analyst]",
        is_cancelled,
    )
    return ContextItem(
        kind=kind,
        label=label,
        text=rendered,
        start_address=function.start,
        truncated=truncated,
    )


def _unique_functions(
    functions: Iterable[Any],
    excluded_start: int,
    limit: int,
    is_cancelled: CancelCheck = None,
    budget: Optional[_TraversalBudget] = None,
) -> list[Function]:
    unique: list[Function] = []
    seen = {excluded_start}
    if limit <= 0:
        return unique
    budget = budget if budget is not None else _TraversalBudget()
    for value in functions:
        if not budget.step(is_cancelled):
            break
        function = getattr(value, "function", value)
        start = getattr(function, "start", None)
        if start is None or start in seen:
            continue
        seen.add(start)
        unique.append(function)
        if len(unique) >= limit:
            break
    return unique


def _callers(
    bv: BinaryView,
    function: Function,
    limit: int,
    is_cancelled: CancelCheck,
    budget: Optional[_TraversalBudget] = None,
) -> list[Function]:
    _check_cancelled(is_cancelled)
    if limit <= 0:
        return []
    try:
        return _unique_functions(
            bv.get_callers(function.start), function.start, limit, is_cancelled, budget,
        )
    except ProviderCancelled:
        raise
    except Exception:
        return []


def _callees(
    bv: BinaryView,
    function: Function,
    limit: int,
    is_cancelled: CancelCheck,
    budget: Optional[_TraversalBudget] = None,
) -> list[Function]:
    _check_cancelled(is_cancelled)
    if limit <= 0:
        return []
    budget = budget if budget is not None else _TraversalBudget()
    direct = getattr(function, "callees", None)
    if direct is not None:
        try:
            if callable(direct):
                direct = direct()
            return _unique_functions(direct, function.start, limit, is_cancelled, budget)
        except ProviderCancelled:
            raise
        except Exception:
            pass

    def discovered() -> Iterator[Function]:
        for call_site in getattr(function, "call_sites", ()):
            if not budget.step(is_cancelled):
                return
            address = getattr(call_site, "address", None)
            if address is None:
                continue
            for target in bv.get_callees(address, function, function.arch):
                if not budget.step(is_cancelled):
                    return
                yield from bv.get_functions_at(target)

    try:
        return _unique_functions(discovered(), function.start, limit, is_cancelled, budget)
    except ProviderCancelled:
        raise
    except Exception:
        return []


def _instruction_addresses(
    function: Function,
    is_cancelled: CancelCheck,
    budget: _TraversalBudget,
) -> Iterator[int]:
    try:
        instructions = function.instructions
    except Exception:
        instructions = ()
    for instruction in instructions:
        if not budget.step(is_cancelled):
            return
        if isinstance(instruction, tuple) and len(instruction) >= 2:
            address = instruction[1]
            if isinstance(address, int):
                yield address


def _referenced_data(
    bv: BinaryView,
    function: Function,
    is_cancelled: CancelCheck,
    budget: Optional[_TraversalBudget] = None,
) -> Iterator[int]:
    budget = budget if budget is not None else _TraversalBudget()
    for address in _instruction_addresses(function, is_cancelled, budget):
        _check_cancelled(is_cancelled)
        try:
            references = bv.get_data_refs_from(address)
        except Exception:
            continue
        for target in references:
            if not budget.step(is_cancelled):
                return
            if isinstance(target, int):
                yield target


def _referenced_code_targets(
    bv: BinaryView,
    function: Function,
    is_cancelled: CancelCheck,
    budget: Optional[_TraversalBudget] = None,
) -> Iterator[int]:
    budget = budget if budget is not None else _TraversalBudget()
    if budget.remaining <= 0:
        budget.exhausted = True
        return
    try:
        for call_site in getattr(function, "call_sites", ()):
            if not budget.step(is_cancelled):
                return
            address = getattr(call_site, "address", None)
            if address is None:
                continue
            for target in bv.get_callees(address, function, function.arch):
                if not budget.step(is_cancelled):
                    return
                if isinstance(target, int):
                    yield target
    except ProviderCancelled:
        raise
    except Exception:
        return


def _bounded_value(value: Any, limit: int, marker: str) -> tuple[str, bool]:
    """Slice host string/byte values before decoding or removing NULs."""
    if limit < 1:
        raise ValueError("max_context_chars must be positive")
    if isinstance(value, bytes):
        raw_limit = (limit + 1) * 4
        source_truncated = len(value) > raw_limit
        text = value[:raw_limit].decode("utf-8", "replace")
    else:
        value = value if isinstance(value, str) else str(value)
        source_truncated = len(value) > limit + 1
        text = value[:limit + 1]
    text = text.replace("\x00", "")
    if source_truncated and len(text) <= limit:
        return _mark_truncated(text, limit, marker)
    return truncate_text(text, limit, marker)


def _search_notice(items: list[ContextItem], kind: str, budget: _TraversalBudget, limit: int) -> None:
    if budget.exhausted and len(items) < limit:
        prefix = "Direct" if kind in ("caller", "callee") else "Referenced"
        label = f"{prefix} {kind} search"
        items.append(ContextItem(
            kind=kind,
            label=label,
            text=f"[{label} truncated after {MAX_REFERENCE_STEPS:,} candidate steps by Axio Analyst]",
            truncated=True,
        ))


def _string_items(
    bv: BinaryView,
    function: Function,
    limit: int,
    text_limit: int,
    is_cancelled: CancelCheck,
) -> list[ContextItem]:
    items: list[ContextItem] = []
    seen: set[int] = set()
    budget = _TraversalBudget()
    if limit <= 0:
        return items
    for target in _referenced_data(bv, function, is_cancelled, budget):
        if target in seen:
            continue
        seen.add(target)
        try:
            reference = bv.get_string_at(target)
        except Exception:
            reference = None
        if reference is None:
            continue
        value = getattr(reference, "value", "")
        label = f"Referenced string 0x{target:x}"
        rendered, truncated = _bounded_value(
            value, text_limit, f"\n\n[{label} truncated by Axio Analyst]",
        )
        if not rendered:
            continue
        items.append(
            ContextItem(
                kind="string",
                label=label,
                text=rendered,
                start_address=target,
                truncated=truncated,
            )
        )
        if len(items) >= limit:
            break
    _search_notice(items, "string", budget, limit)
    return items


def _import_items(
    bv: BinaryView,
    function: Function,
    limit: int,
    text_limit: int,
    is_cancelled: CancelCheck,
) -> list[ContextItem]:
    items: list[ContextItem] = []
    seen: set[int] = set()
    budget = _TraversalBudget()
    if limit <= 0:
        return items
    targets = chain(
        _referenced_data(bv, function, is_cancelled, budget),
        _referenced_code_targets(bv, function, is_cancelled, budget),
    )
    for target in targets:
        if target in seen:
            continue
        seen.add(target)
        try:
            symbol = bv.get_symbol_at(target)
        except Exception:
            symbol = None
        if symbol is None or "import" not in str(getattr(symbol, "type", "")).lower():
            continue
        name = getattr(symbol, "full_name", None) or getattr(symbol, "name", None)
        if not name:
            continue
        label = f"Referenced import 0x{target:x}"
        text, truncated = _bounded_value(
            name, text_limit, f"\n\n[{label} truncated by Axio Analyst]",
        )
        items.append(
            ContextItem(
                kind="import",
                label=label,
                text=text,
                start_address=target,
                truncated=truncated,
            )
        )
        if len(items) >= limit:
            break
    _search_notice(items, "import", budget, limit)
    return items


def _type_item(
    functions: list[Function],
    text_limit: int,
    is_cancelled: CancelCheck,
) -> ContextItem:
    def lines() -> Iterator[str]:
        for function in functions:
            _check_cancelled(is_cancelled)
            yield f"{function.name} at 0x{function.start:x}: {function.type}"

    text, truncated = _bounded_text(
        lines(),
        text_limit,
        "\n\n[Relevant function types truncated by Axio Analyst]",
        is_cancelled,
    )
    return ContextItem(
        kind="types",
        label="Relevant function types",
        text=text,
        start_address=functions[0].start if functions else None,
        truncated=truncated,
    )


def render_context_bundle(
    bv: BinaryView,
    function: Function,
    max_context_chars: int,
    options: ContextOptions = ContextOptions(),
    selection: Optional[tuple[int, int]] = None,
    is_cancelled: CancelCheck = None,
) -> ContextBundle:
    _check_cancelled(is_cancelled)
    architecture = bv.arch.name if bv.arch is not None else "unknown"
    platform = bv.platform.name if bv.platform is not None else "unknown"
    filename = getattr(bv.file, "filename", "") or "unknown"
    extras_requested = any(
        (
            options.include_selection,
            options.include_callers,
            options.include_callees,
            options.include_strings,
            options.include_imports,
            options.include_types,
        )
    )
    primary_limit = (
        min(max_context_chars, max(1000, max_context_chars * 3 // 5))
        if extras_requested
        else max_context_chars
    )
    primary_text, primary_truncated = _bounded_hlil(
        function,
        primary_limit,
        "\n\n[HLIL truncated by Axio Analyst]",
        is_cancelled,
    )
    primary = FunctionContext(
        binary_name=os.path.basename(filename),
        function_name=function.name,
        function_start=function.start,
        architecture=architecture,
        platform=platform,
        function_type=str(function.type),
        hlil=primary_text,
        truncated=primary_truncated,
    )
    candidates = [
        ContextItem(
            kind="current-function",
            label=f"Current function {function.name}",
            text=primary_text,
            start_address=function.start,
            truncated=primary_truncated,
        )
    ]
    per_function_limit = max(1000, min(8000, max_context_chars // 6))
    if options.include_selection and selection is not None:
        start, end = sorted(selection)
        label = f"Selection 0x{start:x}-0x{end:x}"
        text, truncated = _bounded_hlil(
            function,
            max_context_chars,
            f"\n\n[{label} truncated by Axio Analyst]",
            is_cancelled,
            (start, end),
        )
        if text:
            candidates.append(
                ContextItem(
                    kind="selection",
                    label=label,
                    text=text,
                    start_address=start,
                    end_address=end,
                    truncated=truncated,
                )
            )

    caller_budget, callee_budget = _TraversalBudget(), _TraversalBudget()
    callers = (
        _callers(bv, function, options.max_callers, is_cancelled, caller_budget)
        if options.include_callers else []
    )
    callees = (
        _callees(bv, function, options.max_callees, is_cancelled, callee_budget)
        if options.include_callees else []
    )
    caller_items: list[ContextItem] = []
    for caller in callers:
        caller_items.append(
            _function_item(
                caller, "caller", f"Direct caller {caller.name}",
                per_function_limit, is_cancelled,
            )
        )
    _search_notice(caller_items, "caller", caller_budget, options.max_callers)
    candidates.extend(caller_items)
    callee_items: list[ContextItem] = []
    for callee in callees:
        callee_items.append(
            _function_item(
                callee, "callee", f"Direct callee {callee.name}",
                per_function_limit, is_cancelled,
            )
        )
    _search_notice(callee_items, "callee", callee_budget, options.max_callees)
    candidates.extend(callee_items)
    if options.include_strings:
        candidates.extend(
            _string_items(bv, function, options.max_strings, max_context_chars, is_cancelled)
        )
    if options.include_imports:
        candidates.extend(
            _import_items(bv, function, options.max_imports, max_context_chars, is_cancelled)
        )
    if options.include_types:
        candidates.append(
            _type_item([function, *callers, *callees], max_context_chars, is_cancelled)
        )
    _check_cancelled(is_cancelled)
    return build_context_bundle(primary, candidates, max_context_chars)


def render_function_context(
    bv: BinaryView,
    function: Function,
    max_context_chars: int,
) -> FunctionContext:
    """Compatibility wrapper for one-function command integrations."""
    return render_context_bundle(bv, function, max_context_chars).primary

"""Convert Binary Ninja objects into bounded provider-neutral context."""

import os
from collections.abc import Iterable
from typing import Any, Optional

from binaryninja import BinaryView, Function

from ..core.models import (
    ContextBundle,
    ContextItem,
    ContextOptions,
    FunctionContext,
    ProviderError,
)
from ..core.policy import build_context_bundle, truncate_text


def _hlil_lines(function: Function) -> list[tuple[int, str]]:
    hlil = function.hlil
    if hlil is None:
        raise ProviderError(
            f"Binary Ninja could not produce HLIL for {function.name}."
        )
    return [
        (instruction.address, f"0x{instruction.address:x}: {instruction}")
        for instruction in hlil.instructions
    ]


def _function_item(
    function: Function,
    kind: str,
    label: str,
    item_limit: int,
) -> ContextItem:
    rendered, truncated = truncate_text(
        "\n".join(line for _address, line in _hlil_lines(function)),
        item_limit,
        f"\n\n[{label} truncated by Axio Analyst]",
    )
    return ContextItem(
        kind=kind,
        label=label,
        text=rendered,
        start_address=function.start,
        truncated=truncated,
    )


def _unique_functions(functions: Iterable[Any], excluded_start: int) -> list[Function]:
    unique: list[Function] = []
    seen = {excluded_start}
    for value in functions:
        function = getattr(value, "function", value)
        start = getattr(function, "start", None)
        if start is None or start in seen:
            continue
        seen.add(start)
        unique.append(function)
    return unique


def _callers(bv: BinaryView, function: Function) -> list[Function]:
    try:
        return _unique_functions(bv.get_callers(function.start), function.start)
    except Exception:
        return []


def _callees(bv: BinaryView, function: Function) -> list[Function]:
    direct = getattr(function, "callees", None)
    if direct is not None:
        try:
            if callable(direct):
                direct = direct()
            return _unique_functions(direct, function.start)
        except Exception:
            pass

    discovered: list[Function] = []
    try:
        call_sites = getattr(function, "call_sites", ())
        for call_site in call_sites:
            address = getattr(call_site, "address", None)
            if address is None:
                continue
            for target in bv.get_callees(address, function, function.arch):
                discovered.extend(bv.get_functions_at(target))
    except Exception:
        return []
    return _unique_functions(discovered, function.start)


def _instruction_addresses(function: Function) -> tuple[int, ...]:
    addresses: list[int] = []
    seen: set[int] = set()
    try:
        instructions = function.instructions
    except Exception:
        instructions = ()
    for instruction in instructions:
        if not isinstance(instruction, tuple) or len(instruction) < 2:
            continue
        address = instruction[1]
        if isinstance(address, int) and address not in seen:
            seen.add(address)
            addresses.append(address)
    return tuple(addresses)


def _referenced_data(bv: BinaryView, function: Function) -> tuple[int, ...]:
    targets: list[int] = []
    seen: set[int] = set()
    for address in _instruction_addresses(function):
        try:
            references = bv.get_data_refs_from(address)
        except Exception:
            continue
        for target in references:
            if isinstance(target, int) and target not in seen:
                seen.add(target)
                targets.append(target)
    return tuple(targets)


def _referenced_code_targets(bv: BinaryView, function: Function) -> tuple[int, ...]:
    targets: list[int] = []
    seen: set[int] = set()
    try:
        call_sites = getattr(function, "call_sites", ())
        for call_site in call_sites:
            address = getattr(call_site, "address", None)
            if address is None:
                continue
            for target in bv.get_callees(address, function, function.arch):
                if isinstance(target, int) and target not in seen:
                    seen.add(target)
                    targets.append(target)
    except Exception:
        return tuple(targets)
    return tuple(targets)


def _string_items(
    bv: BinaryView,
    function: Function,
    limit: int,
) -> list[ContextItem]:
    items: list[ContextItem] = []
    for target in _referenced_data(bv, function):
        try:
            reference = bv.get_string_at(target)
        except Exception:
            reference = None
        if reference is None:
            continue
        value = getattr(reference, "value", "")
        if isinstance(value, bytes):
            value = value.decode("utf-8", "replace")
        rendered = str(value).replace("\x00", "")
        if not rendered:
            continue
        items.append(
            ContextItem(
                kind="string",
                label=f"Referenced string 0x{target:x}",
                text=rendered,
                start_address=target,
            )
        )
        if len(items) >= limit:
            break
    return items


def _import_items(
    bv: BinaryView,
    function: Function,
    limit: int,
) -> list[ContextItem]:
    items: list[ContextItem] = []
    targets = (
        *_referenced_data(bv, function),
        *_referenced_code_targets(bv, function),
    )
    for target in dict.fromkeys(targets):
        try:
            symbol = bv.get_symbol_at(target)
        except Exception:
            symbol = None
        if symbol is None or "import" not in str(getattr(symbol, "type", "")).lower():
            continue
        name = getattr(symbol, "full_name", None) or getattr(symbol, "name", None)
        if not name:
            continue
        items.append(
            ContextItem(
                kind="import",
                label=f"Referenced import 0x{target:x}",
                text=str(name),
                start_address=target,
            )
        )
        if len(items) >= limit:
            break
    return items


def _type_item(functions: list[Function]) -> ContextItem:
    lines = [f"{function.name} at 0x{function.start:x}: {function.type}" for function in functions]
    return ContextItem(
        kind="types",
        label="Relevant function types",
        text="\n".join(lines),
        start_address=functions[0].start if functions else None,
    )


def render_context_bundle(
    bv: BinaryView,
    function: Function,
    max_context_chars: int,
    options: ContextOptions = ContextOptions(),
    selection: Optional[tuple[int, int]] = None,
) -> ContextBundle:
    lines = _hlil_lines(function)
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
        max(1000, min(max_context_chars, max_context_chars * 3 // 5))
        if extras_requested
        else max_context_chars
    )
    primary_text, primary_truncated = truncate_text(
        "\n".join(line for _address, line in lines),
        primary_limit,
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
        selected = [line for address, line in lines if start <= address < end]
        if selected:
            candidates.append(
                ContextItem(
                    kind="selection",
                    label=f"Selection 0x{start:x}-0x{end:x}",
                    text="\n".join(selected),
                    start_address=start,
                    end_address=end,
                )
            )

    callers = _callers(bv, function) if options.include_callers else []
    callees = _callees(bv, function) if options.include_callees else []
    for caller in callers[: options.max_callers]:
        candidates.append(
            _function_item(
                caller,
                "caller",
                f"Direct caller {caller.name}",
                per_function_limit,
            )
        )
    for callee in callees[: options.max_callees]:
        candidates.append(
            _function_item(
                callee,
                "callee",
                f"Direct callee {callee.name}",
                per_function_limit,
            )
        )
    if options.include_strings:
        candidates.extend(_string_items(bv, function, options.max_strings))
    if options.include_imports:
        candidates.extend(_import_items(bv, function, options.max_imports))
    if options.include_types:
        candidates.append(_type_item([function, *callers, *callees]))

    return build_context_bundle(primary, candidates, max_context_chars)


def render_function_context(
    bv: BinaryView,
    function: Function,
    max_context_chars: int,
) -> FunctionContext:
    """Compatibility wrapper for one-function command integrations."""
    return render_context_bundle(bv, function, max_context_chars).primary

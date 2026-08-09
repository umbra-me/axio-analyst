"""Deterministic request-boundary policies."""

from dataclasses import replace

from .models import ContextBundle, ContextItem, FunctionContext


def truncate_text(
    text: str,
    max_chars: int,
    marker: str = "\n\n[HLIL truncated by Axio Analyst]",
) -> tuple[str, bool]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if len(text) <= max_chars:
        return text, False

    if max_chars <= len(marker):
        return marker[:max_chars], True
    return text[: max_chars - len(marker)].rstrip() + marker, True


def build_context_bundle(
    primary: FunctionContext,
    candidates: list[ContextItem],
    max_chars: int,
) -> ContextBundle:
    """Apply a deterministic total budget, stable ordering, and deduplication."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    remaining = max_chars
    included: list[ContextItem] = []
    seen: set[tuple[str, int | None, str]] = set()
    bundle_truncated = False

    for candidate in candidates:
        key = (candidate.kind, candidate.start_address, candidate.text)
        if key in seen or not candidate.text:
            continue
        seen.add(key)
        if remaining <= 0:
            bundle_truncated = True
            continue

        marker = f"\n\n[{candidate.label} truncated by Axio Analyst]"
        rendered, truncated = truncate_text(candidate.text, remaining, marker)
        included.append(
            replace(
                candidate,
                text=rendered,
                truncated=candidate.truncated or truncated,
            )
        )
        remaining -= len(rendered)
        bundle_truncated = bundle_truncated or candidate.truncated or truncated

    return ContextBundle(
        primary=primary,
        items=tuple(included),
        max_chars=max_chars,
        truncated=bundle_truncated,
    )

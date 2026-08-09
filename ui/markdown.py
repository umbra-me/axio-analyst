"""Safe text preparation for the native conversation renderer."""

import html


def safe_markdown(value: str) -> str:
    """Preserve Markdown while preventing provider-supplied raw HTML."""
    return html.escape(value.replace("\x00", ""), quote=False)


def restored_scroll_value(
    previous_value: int,
    previous_maximum: int,
    new_maximum: int,
    force_bottom: bool = False,
) -> int:
    """Follow a live tail only when the reader was already at the bottom."""
    was_at_bottom = previous_value >= previous_maximum - 24
    if force_bottom or was_at_bottom:
        return new_maximum
    return min(previous_value, new_maximum)

"""Safe text preparation for the native conversation renderer.

Raw provider HTML is neutralised by the Markdown parser itself: the transcript
imports with ``QTextDocument.MarkdownNoHTML``, so md4c never emits an HTML
block or span and a tag can only ever appear as inert literal text. That is
stronger than escaping the source string, and unlike escaping it does not leak
``&gt;`` and ``&lt;`` into fenced code blocks, where CommonMark does not decode
entities. This module only removes control characters that would otherwise
corrupt the imported document.
"""

_ALLOWED_CONTROLS = {"\n", "\t"}


def sanitize_markdown(value: str) -> str:
    """Drop control characters while leaving every Markdown construct intact."""
    return "".join(
        character
        for character in value
        if character in _ALLOWED_CONTROLS or ord(character) >= 0x20
    )


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

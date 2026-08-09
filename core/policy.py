"""Deterministic request-boundary policies."""


def truncate_text(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")
    if len(text) <= max_chars:
        return text, False

    marker = "\n\n[HLIL truncated by Axio Analyst]"
    if max_chars <= len(marker):
        return marker[:max_chars], True
    return text[: max_chars - len(marker)].rstrip() + marker, True

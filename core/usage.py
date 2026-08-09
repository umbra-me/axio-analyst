"""Provider-neutral presentation of request accounting."""

from .models import ProviderUsage


def format_usage(usage: ProviderUsage) -> str:
    parts = [f"{usage.duration_seconds:.1f}s"]
    if usage.input_tokens is not None or usage.output_tokens is not None:
        input_tokens = "?" if usage.input_tokens is None else f"{usage.input_tokens:,}"
        output_tokens = "?" if usage.output_tokens is None else f"{usage.output_tokens:,}"
        parts.append(f"{input_tokens} in / {output_tokens} out tokens")
    else:
        parts.append(f"{usage.input_chars:,} in / {usage.output_chars:,} out chars")
    if usage.cached_input_tokens is not None:
        parts.append(f"{usage.cached_input_tokens:,} cached")
    if usage.cost_usd is not None:
        parts.append(f"${usage.cost_usd:.4f}")
    return "  ·  ".join(parts)

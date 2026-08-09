"""Analyze a prepared context snapshot through an injected provider."""

import time
from dataclasses import replace
from typing import Callable, Optional

from ..core.models import ContextBundle, FunctionContext, ProviderResult
from ..core.prompts import build_prompt
from ..core.provider import CancelCheck, Provider, StreamCallback


def analyze(
    context: FunctionContext | ContextBundle,
    question: str,
    provider: Provider,
    is_cancelled: CancelCheck = None,
    on_stream: StreamCallback = None,
    on_provider_start: Optional[Callable[[], None]] = None,
) -> ProviderResult:
    prompt = build_prompt(context, question)
    if on_provider_start is not None:
        on_provider_start()
    started = time.monotonic()
    result = provider.complete(prompt, is_cancelled, on_stream)
    elapsed = time.monotonic() - started
    usage = replace(
        result.usage,
        input_chars=result.usage.input_chars or len(prompt),
        output_chars=result.usage.output_chars or len(result.text),
        duration_seconds=result.usage.duration_seconds or elapsed,
    )
    return replace(result, usage=usage)

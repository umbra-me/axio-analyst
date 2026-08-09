"""Analyze a prepared function context through an injected provider."""

from typing import Callable, Optional

from ..core.models import FunctionContext, ProviderResult
from ..core.prompts import build_prompt
from ..core.provider import CancelCheck, Provider, StreamCallback


def analyze(
    context: FunctionContext,
    question: str,
    provider: Provider,
    is_cancelled: CancelCheck = None,
    on_stream: StreamCallback = None,
    on_provider_start: Optional[Callable[[], None]] = None,
) -> ProviderResult:
    prompt = build_prompt(context, question)
    if on_provider_start is not None:
        on_provider_start()
    return provider.complete(prompt, is_cancelled, on_stream)

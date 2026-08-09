"""Binary Ninja background tasks for context preview and analysis."""

import time
from typing import Callable, Optional

from binaryninja import BackgroundTaskThread, BinaryView, Function
from binaryninja.interaction import show_plain_text_report
from binaryninja.log import log_error, log_info, log_warn
from binaryninja.mainthread import execute_on_main_thread

from ..application import analyze
from ..core.models import (
    ContextBundle,
    ContextOptions,
    ProviderCancelled,
    ProviderConfig,
    ProviderError,
    ProviderResult,
)
from ..providers import create_provider
from .context import render_context_bundle
from .settings import BACKEND_LABELS, RuntimeConfig

TITLE = "Axio Analyst"

CompleteCallback = Callable[[ContextBundle, tuple[ProviderResult, ...]], None]
ContextCallback = Callable[[ContextBundle], None]
ErrorCallback = Callable[[str], None]
CancelledCallback = Callable[[], None]
ProgressCallback = Callable[[str, int], None]
StreamCallback = Callable[[str], None]


def _dispatch(callback: Optional[Callable[..., None]], *args: object) -> None:
    if callback is None:
        return

    def invoke() -> None:
        try:
            callback(*args)
        except RuntimeError:
            pass
        except Exception as exc:
            log_error(f"{TITLE}: result callback failed: {exc}")

    execute_on_main_thread(invoke)


class ContextPreviewTask(BackgroundTaskThread):
    def __init__(
        self,
        bv: BinaryView,
        function: Function,
        max_context_chars: int,
        options: ContextOptions,
        selection: Optional[tuple[int, int]],
        on_complete: ContextCallback,
        on_error: ErrorCallback,
    ):
        super().__init__(f"{TITLE}: previewing context", can_cancel=True)
        self.bv = bv
        self.function = function
        self.max_context_chars = max_context_chars
        self.options = options
        self.selection = selection
        self.on_complete = on_complete
        self.on_error = on_error

    def run(self) -> None:
        try:
            bundle = render_context_bundle(
                self.bv,
                self.function,
                self.max_context_chars,
                self.options,
                self.selection,
            )
            if not self.cancelled:
                _dispatch(self.on_complete, bundle)
        except Exception as exc:
            _dispatch(self.on_error, str(exc))


class AnalyzeFunctionTask(BackgroundTaskThread):
    def __init__(
        self,
        bv: BinaryView,
        function: Function,
        question: str,
        config: RuntimeConfig,
        show_report: bool = True,
        on_complete: Optional[CompleteCallback] = None,
        on_error: Optional[ErrorCallback] = None,
        on_cancelled: Optional[CancelledCallback] = None,
        on_progress: Optional[ProgressCallback] = None,
        on_stream: Optional[StreamCallback] = None,
        on_context: Optional[ContextCallback] = None,
        context_options: ContextOptions = ContextOptions(),
        selection: Optional[tuple[int, int]] = None,
        comparison_provider: Optional[ProviderConfig] = None,
    ):
        super().__init__(f"{TITLE}: preparing {function.name}", can_cancel=True)
        self.bv = bv
        self.function = function
        self.question = question
        self.config = config
        self.show_report = show_report
        self.on_complete = on_complete
        self.on_error = on_error
        self.on_cancelled = on_cancelled
        self.on_progress = on_progress
        self.on_stream = on_stream
        self.on_context = on_context
        self.context_options = context_options
        self.selection = selection
        self.comparison_provider = comparison_provider
        self._pending_stream = ""
        self._last_stream_dispatch = 0.0

    def _set_progress(self, message: str, value: int) -> None:
        self.progress = f"{TITLE}: {message.lower()}"
        _dispatch(self.on_progress, message, value)

    def _stream(self, text: str) -> None:
        if not text:
            return
        self._pending_stream += text
        now = time.monotonic()
        if len(self._pending_stream) >= 512 or now - self._last_stream_dispatch >= 0.06:
            self._flush_stream(now)

    def _flush_stream(self, now: Optional[float] = None) -> None:
        if not self._pending_stream:
            return
        chunk = self._pending_stream
        self._pending_stream = ""
        self._last_stream_dispatch = now if now is not None else time.monotonic()
        _dispatch(self.on_stream, chunk)

    def run(self) -> None:
        try:
            self._set_progress("Building context snapshot", 10)
            context = render_context_bundle(
                self.bv,
                self.function,
                self.config.max_context_chars,
                self.context_options,
                self.selection,
            )
            _dispatch(self.on_context, context)
            if self.cancelled:
                raise ProviderCancelled("Request cancelled before dispatch.")

            provider_configs = [self.config.provider]
            if (
                self.comparison_provider is not None
                and self.comparison_provider.backend != self.config.provider.backend
            ):
                provider_configs.append(self.comparison_provider)

            results: list[ProviderResult] = []
            for index, provider_config in enumerate(provider_configs):
                if self.cancelled:
                    raise ProviderCancelled("Request cancelled before dispatch.")
                label = BACKEND_LABELS.get(
                    provider_config.backend,
                    provider_config.backend,
                )
                progress = 35 if index == 0 else 68
                self._set_progress(f"Starting {label}", progress)
                try:
                    result = analyze(
                        context,
                        self.question,
                        create_provider(provider_config),
                        is_cancelled=lambda: self.cancelled,
                        on_stream=self._stream if index == 0 else None,
                    )
                except ProviderCancelled:
                    raise
                except ProviderError as exc:
                    if len(provider_configs) == 1:
                        raise
                    result = ProviderResult(
                        text="",
                        backend=provider_config.backend,
                        model=provider_config.model,
                        reasoning_effort=provider_config.reasoning_effort,
                        error=str(exc),
                    )
                results.append(result)
                if index == 0:
                    self._flush_stream()

            self._set_progress("Finalizing response", 90)
            result_tuple = tuple(results)
            if self.show_report:
                report_title = f"{TITLE} - {context.primary.function_name}"
                report_parts = []
                for result in result_tuple:
                    label = BACKEND_LABELS.get(result.backend, result.backend)
                    report_parts.append(
                        f"{label}\n{'=' * len(label)}\n{result.text or result.error}"
                    )
                report_text = "\n\n".join(report_parts)
                execute_on_main_thread(
                    lambda: show_plain_text_report(report_title, report_text)
                )
            _dispatch(self.on_complete, context, result_tuple)
            labels = ", ".join(result.backend for result in result_tuple)
            log_info(f"{TITLE}: completed with {labels}.")
        except ProviderCancelled:
            self._flush_stream()
            log_warn(f"{TITLE}: request cancelled.")
            _dispatch(self.on_cancelled)
        except ProviderError as exc:
            self._flush_stream()
            log_error(f"{TITLE}: {exc}")
            _dispatch(self.on_error, str(exc))
        except Exception as exc:
            self._flush_stream()
            log_error(f"{TITLE}: unexpected failure: {exc}")
            _dispatch(self.on_error, f"Unexpected failure: {exc}")

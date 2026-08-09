"""Binary Ninja background task for one analysis request."""

import time
from typing import Callable, Optional

from binaryninja import BackgroundTaskThread, BinaryView, Function
from binaryninja.interaction import show_plain_text_report
from binaryninja.log import log_error, log_info, log_warn
from binaryninja.mainthread import execute_on_main_thread

from ..application import analyze
from ..core.models import (
    FunctionContext,
    ProviderCancelled,
    ProviderError,
    ProviderResult,
)
from ..providers import create_provider
from .context import render_function_context
from .settings import RuntimeConfig

TITLE = "Axio Analyst"

CompleteCallback = Callable[[FunctionContext, ProviderResult], None]
ErrorCallback = Callable[[str], None]
CancelledCallback = Callable[[], None]
ProgressCallback = Callable[[str, int], None]
StreamCallback = Callable[[str], None]


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
        self._pending_stream = ""
        self._last_stream_dispatch = 0.0

    @staticmethod
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

    def _set_progress(self, message: str, value: int) -> None:
        self.progress = f"{TITLE}: {message.lower()}"
        self._dispatch(self.on_progress, message, value)

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
        self._dispatch(self.on_stream, chunk)

    def run(self) -> None:
        try:
            self._set_progress("Rendering HLIL", 10)
            context = render_function_context(
                self.bv,
                self.function,
                self.config.max_context_chars,
            )
            if self.cancelled:
                raise ProviderCancelled("Request cancelled before dispatch.")

            self._set_progress("Building request", 25)
            provider = create_provider(self.config.provider)
            result = analyze(
                context,
                self.question,
                provider,
                is_cancelled=lambda: self.cancelled,
                on_stream=self._stream,
                on_provider_start=lambda: self._set_progress(
                    "Starting provider",
                    40,
                ),
            )
            self._flush_stream()
            self._set_progress("Finalizing response", 90)

            if self.show_report:
                report_title = f"{TITLE} - {context.function_name}"
                report_text = result.text
                execute_on_main_thread(
                    lambda: show_plain_text_report(report_title, report_text)
                )
            self._dispatch(self.on_complete, context, result)
            model = f" ({result.model})" if result.model else ""
            log_info(f"{TITLE}: completed with {result.backend}{model}.")
        except ProviderCancelled:
            self._flush_stream()
            log_warn(f"{TITLE}: request cancelled.")
            self._dispatch(self.on_cancelled)
        except ProviderError as exc:
            self._flush_stream()
            log_error(f"{TITLE}: {exc}")
            self._dispatch(self.on_error, str(exc))
        except Exception as exc:
            self._flush_stream()
            log_error(f"{TITLE}: unexpected failure: {exc}")
            self._dispatch(self.on_error, f"Unexpected failure: {exc}")

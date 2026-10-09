"""Native Binary Ninja sidebar controller for Axio Analyst."""

import os
from pathlib import Path
from typing import Optional

from binaryninja import BinaryView, Function
from binaryninjaui import (
    Sidebar,
    SidebarWidget,
    SidebarWidgetLocation,
    SidebarWidgetType,
    UIContext,
    ViewFrame,
)
from PySide6 import QtCore, QtWidgets

from ..application import ConversationMessage, ConversationStore, new_record
from ..core.evidence import classify_evidence
from ..core.findings import build_findings
from ..core.version import VERSION
from ..core.models import ContextBundle, ProviderConfig, ProviderResult
from ..core.prompts import DEFAULT_QUESTION, render_context
from ..core.usage import format_usage
from ..host.model_discovery import OllamaModelDiscovery
from ..host.settings import (
    BACKEND_LABELS,
    RuntimeConfig,
    get_provider_config,
    get_runtime_config,
)
from ..host.storage import binary_fingerprint, conversation_store
from ..host.task import AnalyzeFunctionTask, ContextPreviewTask
from . import branding
from .progress import RequestProgress
from .sidebar_view import SidebarView
from .transcript import Transcript

WIDGET_NAME = "Axio Analyst"


class AxioAnalystSidebar(SidebarWidget):
    """Conversation controller scoped to the function under the cursor."""

    def __init__(self, name: str, frame: ViewFrame, data: BinaryView):
        SidebarWidget.__init__(self, name)
        self.m_actionHandler.setupActionHandler(self)

        self.frame: Optional[ViewFrame] = frame
        self.bv: Optional[BinaryView] = data
        self._current_function: Optional[Function] = None
        self._task: Optional[AnalyzeFunctionTask] = None
        self._preview_task: Optional[ContextPreviewTask] = None
        self._alive = True
        self._request_generation = 0
        self._preview_generation = 0
        self._binary_id = ""
        try:
            self._conversation_store = conversation_store()
        except OSError:
            self._conversation_store = None

        self.view = SidebarView(self)
        root = QtWidgets.QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.view)
        self.setLayout(root)

        self._provider_summary = ""
        self.conversation = Transcript(self.view.transcript)
        self.request_progress = RequestProgress(
            self.view.progress_bar,
            self.view.status_line.message,
            self.view.status_line.elapsed,
            lambda: self._task is not None,
            self,
        )
        self.model_discovery = OllamaModelDiscovery(self)
        self.model_discovery.busyChanged.connect(self._update_actions)
        self.model_discovery.modelsReady.connect(self._ollama_models_ready)
        self.model_discovery.statusChanged.connect(self._discovery_status_changed)
        self.view.askRequested.connect(self._ask)
        self.view.clearRequested.connect(self._clear_transcript)
        self.view.exportRequested.connect(self._export_transcript)
        self.view.explainRequested.connect(self._explain)
        self.view.previewRequested.connect(self._preview_context)
        self.view.contextOptionsChanged.connect(self._invalidate_context_preview)
        self.view.stopRequested.connect(self._cancel)
        self.view.suggestionChosen.connect(self._ask_suggestion)
        self.view.prompt.textChanged.connect(self._update_actions)
        self.view.transcript.anchorClicked.connect(self._navigate_evidence)
        self.view.settings_page.providerChanged.connect(
            self._settings_provider_changed
        )
        self.view.settings_page.applied.connect(self._settings_applied)
        self.view.settings_page.refreshModelsRequested.connect(
            self._discover_ollama_models
        )

        self.destroyed.connect(self._mark_dead)
        self._load_transcript()
        self._refresh_backend_label()
        self.view.refresh_scope_disclosure()
        self._update_actions()
        if self._selected_backend() == "ollama-cloud":
            self._discover_ollama_models()
        self._refresh_from_frame()

    def _selected_backend(self) -> str:
        return self.view.settings_page.selected_backend()

    def _settings_provider_changed(self, backend: str) -> None:
        if self.view.selected_comparison_backend() == backend:
            self.view.clear_comparison()
        self._update_actions()
        if backend == "ollama-cloud":
            self._discover_ollama_models()

    def _settings_applied(self) -> None:
        self._invalidate_context_preview()
        self._refresh_backend_label()
        if self._selected_backend() == "ollama-cloud":
            self.model_discovery.refresh(
                self.view.settings_page.selected_ollama_executable()
            )
        self._update_actions()

    def _save_selection(self, *_args: object) -> None:
        self.view.settings_page.save_selection()
        self._refresh_backend_label()

    def _discover_ollama_models(self, *_args: object) -> None:
        if self._selected_backend() != "ollama-cloud":
            return
        self._save_selection()
        self.model_discovery.refresh(
            self.view.settings_page.selected_ollama_executable()
        )
        self._update_actions()

    def _ollama_models_ready(self, models: list[str]) -> None:
        if self._alive and self._selected_backend() == "ollama-cloud":
            self.view.settings_page.replace_ollama_models(models)

    def _discovery_status_changed(self, message: str) -> None:
        if self._alive and self._selected_backend() == "ollama-cloud":
            self.view.settings_page.set_status(message)

    def _mark_dead(self, *_args: object) -> None:
        self._alive = False
        self._request_generation += 1
        self._preview_generation += 1
        self.request_progress.stop()
        self.model_discovery.close()
        if self._task is not None:
            self._task.cancel()
        if self._preview_task is not None:
            self._preview_task.cancel()

    def _clear_transcript(self) -> None:
        if self._task is None:
            self.conversation.reset()
            if self._binary_id and self._conversation_store is not None:
                try:
                    self._conversation_store.delete(self._binary_id)
                except (OSError, ValueError) as exc:
                    self.view.status_line.message.setText(
                        f"Could not delete saved conversation: {exc}"
                    )

    def _load_transcript(self) -> None:
        self.conversation.reset()
        self._binary_id = ""
        if self.bv is None:
            return
        try:
            self._binary_id = binary_fingerprint(self.bv)
            if (
                not get_runtime_config().persist_conversations
                or self._conversation_store is None
            ):
                return
            record = self._conversation_store.load(self._binary_id)
            if record is not None and record.messages:
                revalidated = []
                for message in record.messages:
                    evidence, unresolved = (
                        classify_evidence(message.body, self._is_valid_address)
                        if message.role == "Axio Analyst"
                        else ((), ())
                    )
                    revalidated.append(
                        ConversationMessage(
                            role=message.role,
                            body=message.body,
                            meta=message.meta,
                            evidence=evidence,
                            unresolved_evidence=unresolved,
                            findings=message.findings,
                        )
                    )
                self.conversation.load(tuple(revalidated))
                self.view.status_line.message.setText("Restored local conversation")
        except (OSError, ValueError) as exc:
            self.view.status_line.message.setText(f"Could not restore conversation: {exc}")

    def _persist_transcript(self) -> None:
        if (
            self.bv is None
            or not self._binary_id
            or self._conversation_store is None
        ):
            return
        try:
            if not get_runtime_config().persist_conversations:
                return
            filename = getattr(self.bv.file, "filename", "") or "binary"
            record = new_record(
                self._binary_id,
                os.path.basename(filename),
                self.conversation.snapshot(),
            )
            self._conversation_store.save(record)
        except (OSError, ValueError) as exc:
            self.view.status_line.message.setText(f"Could not save conversation: {exc}")

    def _export_transcript(self) -> None:
        if self.bv is None or not self._binary_id:
            return
        filename = getattr(self.bv.file, "filename", "") or "binary"
        suggested = f"{Path(filename).stem}-axio-analyst.md"
        path, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Axio Analyst conversation",
            suggested,
            "Markdown (*.md)",
        )
        if not path:
            return
        try:
            record = new_record(
                self._binary_id,
                os.path.basename(filename),
                self.conversation.snapshot(),
            )
            ConversationStore.export_markdown(record, Path(path))
            self.view.status_line.message.setText(f"Exported conversation to {path}")
        except (OSError, ValueError) as exc:
            self.view.status_line.message.setText(f"Could not export conversation: {exc}")

    def _analysis_stream(self, chunk: str) -> None:
        if self._alive and self.conversation.stream(chunk):
            self.view.status_line.message.setText("Receiving response...")

    def _refresh_backend_label(self, config: Optional[RuntimeConfig] = None) -> None:
        active = config or get_runtime_config()
        model = active.provider.model or "default model"
        backend = BACKEND_LABELS.get(active.provider.backend, active.provider.backend)
        self._provider_summary = f"{backend} · {model}"
        self._refresh_scope()

    def _refresh_scope(self) -> None:
        """The empty state answers what will run before the first request."""
        function = self._current_function
        if function is None:
            self.view.set_scope(
                "No function selected",
                "",
                "Move the cursor into a function to begin.",
                False,
            )
            return
        architecture = (
            self.bv.arch.name
            if self.bv is not None and self.bv.arch is not None
            else "unknown architecture"
        )
        address = f"0x{function.start:x}"
        detail = f"{address} · {architecture} · {self._provider_summary}"
        self.view.set_scope(function.name, address, detail, True)

    def _refresh_from_frame(self) -> None:
        if self.frame is None:
            self._replace_binary_view(None)
            self._set_current_function(None)
            return
        try:
            view = self.frame.getCurrentViewInterface()
            if view is None:
                self._replace_binary_view(None)
                self._set_current_function(None)
                return
            data = view.getData()
            self._replace_binary_view(data)
            self._set_function_for_offset(view.getCurrentOffset())
        except Exception:
            self._replace_binary_view(None)
            self._set_current_function(None)

    def _replace_binary_view(self, data: Optional[BinaryView]) -> None:
        if data is not self.bv:
            self._detach_request()
            self._invalidate_context_preview()
            self.bv = data
            self._load_transcript()

    def _set_function_for_offset(self, offset: int) -> None:
        if self.bv is None:
            self._set_current_function(None)
            return
        functions = self.bv.get_functions_containing(offset)
        self._set_current_function(functions[0] if functions else None)

    def _set_current_function(self, function: Optional[Function]) -> None:
        changed = (
            function is not self._current_function
            and (
                function is None
                or self._current_function is None
                or function.start != self._current_function.start
            )
        )
        self._current_function = function
        self._refresh_scope()
        if changed:
            self._invalidate_context_preview()
        self._update_actions()

    def _invalidate_context_preview(self, *_args: object) -> None:
        self._preview_generation += 1
        if self._preview_task is not None:
            self._preview_task.cancel()
            self._preview_task = None
        self.view.set_context_snapshot("Preview not built", "")
        self.view.refresh_scope_disclosure()
        self._update_actions()

    def _detach_request(self) -> None:
        """Reject queued callbacks before replacing the active binary/conversation."""
        self._request_generation += 1
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self.request_progress.stop()
        self.view.status_line.release()

    def _request_callback(self, callback):
        generation, binary_view = self._request_generation, self.bv

        def deliver(*args):
            if (self._alive and self._task is not None
                    and generation == self._request_generation and self.bv is binary_view):
                callback(*args)
        return deliver

    def _preview_callback(self, callback):
        generation, binary_view = self._preview_generation, self.bv

        def deliver(*args):
            if (self._alive and self._preview_task is not None
                    and generation == self._preview_generation and self.bv is binary_view):
                callback(*args)
        return deliver

    def _current_selection(self) -> Optional[tuple[int, int]]:
        if self.frame is None:
            return None
        try:
            view = self.frame.getCurrentViewInterface()
            if view is None:
                return None
            getter = getattr(view, "getSelectionOffsets", None)
            if getter is None:
                getter = getattr(view, "getCurrentSelection", None)
            if getter is None:
                return None
            selection = getter()
            if isinstance(selection, (tuple, list)) and len(selection) >= 2:
                start, end = selection[0], selection[1]
            else:
                start = getattr(selection, "start", None)
                end = getattr(selection, "end", None)
            if isinstance(start, int) and isinstance(end, int) and start != end:
                return start, end
        except Exception:
            return None
        return None

    @staticmethod
    def _context_summary(context: ContextBundle) -> str:
        suffix = " · truncated" if context.truncated else ""
        return (
            f"{len(context.items)} item{'s' if len(context.items) != 1 else ''}"
            f" · {context.total_chars:,} chars{suffix}"
        )

    def _context_ready(self, context: ContextBundle) -> None:
        if not self._alive:
            return
        self.view.set_context_snapshot(
            self._context_summary(context),
            render_context(context),
        )
        self._preview_task = None
        if self._task is None:
            self.view.status_line.message.setText("Context preview is current")
        self._update_actions()

    def _preview_error(self, message: str) -> None:
        if not self._alive:
            return
        self._preview_task = None
        self.view.status_line.message.setText(f"Could not build context preview: {message}")
        self._update_actions()

    def _preview_context(self) -> None:
        if (
            self._task is not None
            or self._preview_task is not None
            or self._current_function is None
            or self.bv is None
        ):
            return
        config = get_runtime_config()
        self._preview_generation += 1
        self.view.status_line.message.setText("Building exact context preview...")
        self._preview_task = ContextPreviewTask(
            self.bv,
            self._current_function,
            config.max_context_chars,
            self.view.selected_context_options(),
            self._current_selection(),
            self._preview_callback(self._context_ready),
            self._preview_callback(self._preview_error),
        )
        self._update_actions()
        self._preview_task.start()

    def _update_actions(self, *_args: object) -> None:
        busy = self._task is not None or self._preview_task is not None
        ready = self._current_function is not None and not busy
        self.view.explain_action.setEnabled(ready)
        self.view.ask_button.setEnabled(
            ready and bool(self.view.prompt.toPlainText().strip())
        )
        self.view.stop_button.setEnabled(self._task is not None)
        self.view.set_conversation_empty(not self.conversation.messages)
        self.view.clear_action.setEnabled(not busy)
        self.view.export_action.setEnabled(
            not busy and bool(self.conversation.messages)
        )
        self.view.preview_button.setEnabled(ready)
        self.view.set_comparison_enabled(not busy)
        self.view.submit_action.setCurrentWidget(
            self.view.stop_button if self._task is not None else self.view.ask_button
        )
        self.view.settings_page.set_busy(
            busy,
            self.model_discovery.busy,
        )

    def _explain(self) -> None:
        self._start_request(DEFAULT_QUESTION, "Explain this function.")

    def _ask(self) -> None:
        question = self.view.prompt.toPlainText().strip()
        if question:
            self._start_request(question, question)

    def _ask_suggestion(self, question: str) -> None:
        if self._task is None and self._current_function is not None:
            self._start_request(question, question)

    def _start_request(self, question: str, display_question: str) -> None:
        if self._task is not None or self._current_function is None or self.bv is None:
            return

        self._invalidate_context_preview()
        self._request_generation += 1
        self._save_selection()
        config = get_runtime_config()
        function = self._current_function
        self.conversation.append("You", display_question)
        self._persist_transcript()
        backend = BACKEND_LABELS.get(config.provider.backend, config.provider.backend)
        model = config.provider.model or "default model"
        self.conversation.start_response(f"{backend} · {model}")
        self.view.prompt.clear()
        self._refresh_backend_label(config)
        self.view.status_line.hold()
        self.request_progress.begin(f"Preparing {function.name} with {backend}...")

        self._task = AnalyzeFunctionTask(
            self.bv,
            function,
            question,
            config,
            show_report=False,
            on_complete=self._request_callback(self._analysis_complete),
            on_error=self._request_callback(self._analysis_error),
            on_cancelled=self._request_callback(self._analysis_cancelled),
            on_progress=self._request_callback(self.request_progress.update),
            on_stream=self._request_callback(self._analysis_stream),
            on_context=self._request_callback(self._context_ready),
            context_options=self.view.selected_context_options(),
            selection=self._current_selection(),
            comparison_provider=self._comparison_provider(config),
        )
        self._update_actions()
        self._task.start()

    def _comparison_provider(
        self,
        config: RuntimeConfig,
    ) -> Optional[ProviderConfig]:
        backend = self.view.selected_comparison_backend()
        if not backend or backend == config.provider.backend:
            return None
        try:
            return get_provider_config(backend)
        except ValueError:
            return None

    def _cancel(self) -> None:
        if self._task is None:
            return
        self.view.status_line.message.setText("Cancelling request...")
        self.view.stop_button.setEnabled(False)
        self._task.cancel()

    def _analysis_complete(
        self,
        context: ContextBundle,
        results: tuple[ProviderResult, ...],
    ) -> None:
        if not self._alive:
            return
        sections: list[str] = []
        metadata: list[str] = []
        for result in results:
            model = result.model or "default model"
            effort = result.reasoning_effort or "default effort"
            backend = BACKEND_LABELS.get(result.backend, result.backend)
            heading = f"## {backend} · {model} · {effort}" if len(results) > 1 else ""
            failure_label = "Request cancelled" if result.cancelled else "Request failed"
            body = result.text if not result.error else f"**{failure_label}:** {result.error}"
            sections.append(f"{heading}\n\n{body}".strip())
            metadata.append(f"{backend}: {format_usage(result.usage)}")
        response = "\n\n---\n\n".join(sections)
        findings = tuple(finding for result in results if not result.error
                         for finding in build_findings(result.text, context, VERSION, result.backend, result.model))[:64]
        if findings:
            metadata.append(f"{len(findings)} unverified finding(s) · context {findings[0].context_sha256[:12]}")
        evidence, unresolved = classify_evidence(response, self._is_valid_address)
        self.conversation.complete(
            response,
            "   ·   ".join(metadata),
            evidence,
            unresolved,
            findings,
        )
        self._task = None
        self._persist_transcript()
        cancelled = any(result.cancelled for result in results)
        status = "Complete with provider errors" if any(
            result.error for result in results
        ) else "Complete"
        if cancelled:
            status = "Comparison cancelled; completed results retained"
        self.view.status_line.release()
        self.request_progress.finish(status, completed=not cancelled)
        self._update_actions()

    def _analysis_error(self, message: str) -> None:
        if not self._alive:
            return
        self.conversation.fail(message)
        self._task = None
        self._persist_transcript()
        self.view.status_line.release()
        self.request_progress.finish("Request failed. Check the message above.")
        self._update_actions()

    def _analysis_cancelled(self) -> None:
        if not self._alive:
            return
        self.conversation.cancel()
        self._task = None
        self._persist_transcript()
        self.view.status_line.release()
        self.request_progress.finish("Request cancelled")
        self._update_actions()

    def notifyOffsetChanged(self, offset: int) -> None:
        self._invalidate_context_preview()
        self._set_function_for_offset(offset)

    def notifyViewChanged(self, view_frame: Optional[ViewFrame]) -> None:
        self.frame = view_frame
        self._refresh_from_frame()

    def _is_valid_address(self, address: int) -> bool:
        if self.bv is None:
            return False
        try:
            validator = getattr(self.bv, "is_valid_offset", None)
            if validator is not None:
                return bool(validator(address))
            return 0 <= address < int(self.bv.length)
        except Exception:
            return False

    def _navigate_evidence(self, url: QtCore.QUrl) -> None:
        if url.scheme() != "axio" or url.host() != "address":
            return
        try:
            address = int(url.path().strip("/"), 16)
        except ValueError:
            return
        if not self._is_valid_address(address) or self.frame is None:
            self.view.status_line.message.setText(f"Address 0x{address:x} is not valid")
            return
        try:
            view = self.frame.getCurrentViewInterface()
            navigator = getattr(view, "navigate", None) if view is not None else None
            if navigator is not None:
                navigator(address)
                self.view.status_line.message.setText(f"Navigated to 0x{address:x}")
                return
            if self.bv is not None:
                current_view = self.frame.getCurrentView()
                self.bv.navigate(current_view, address)
                self.view.status_line.message.setText(f"Navigated to 0x{address:x}")
        except Exception as exc:
            self.view.status_line.message.setText(
                f"Could not navigate to 0x{address:x}: {exc}"
            )


class AxioAnalystSidebarType(SidebarWidgetType):
    def __init__(self):
        SidebarWidgetType.__init__(self, branding.sidebar_icon(), WIDGET_NAME)

    def createWidget(self, frame: ViewFrame, data: BinaryView) -> SidebarWidget:
        return AxioAnalystSidebar(WIDGET_NAME, frame, data)

    def defaultLocation(self) -> SidebarWidgetLocation:
        return SidebarWidgetLocation.RightContent


def open_sidebar() -> bool:
    context = UIContext.activeContext()
    if context is None or context.sidebar() is None:
        return False
    context.sidebar().activate(WIDGET_NAME)
    return True


def register_sidebar() -> None:
    Sidebar.addSidebarWidgetType(AxioAnalystSidebarType())

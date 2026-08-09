"""Native Binary Ninja sidebar controller for Axio Analyst."""

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
from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import FunctionContext, ProviderResult
from ..core.prompts import DEFAULT_QUESTION
from ..host.model_discovery import OllamaModelDiscovery
from ..host.settings import BACKEND_LABELS, RuntimeConfig, get_runtime_config
from ..host.task import AnalyzeFunctionTask
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
        self._alive = True

        self.view = SidebarView(self)
        root = QtWidgets.QVBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.view)
        self.setLayout(root)

        self.conversation = Transcript(self.view.transcript)
        self.request_progress = RequestProgress(
            self.view.progress_bar,
            self.view.status_label,
            self.view.elapsed_label,
            lambda: self._task is not None,
            self,
        )
        self.model_discovery = OllamaModelDiscovery(self)
        self.model_discovery.busyChanged.connect(self._update_actions)
        self.model_discovery.modelsReady.connect(self._ollama_models_ready)
        self.model_discovery.statusChanged.connect(self._discovery_status_changed)
        self.view.askRequested.connect(self._ask)
        self.view.clearRequested.connect(self._clear_transcript)
        self.view.explainRequested.connect(self._explain)
        self.view.stopRequested.connect(self._cancel)
        self.view.prompt.textChanged.connect(self._update_actions)
        self.view.settings_page.providerChanged.connect(
            self._settings_provider_changed
        )
        self.view.settings_page.applied.connect(self._settings_applied)
        self.view.settings_page.refreshModelsRequested.connect(
            self._discover_ollama_models
        )

        self.destroyed.connect(self._mark_dead)
        self._clear_transcript()
        self._refresh_backend_label()
        self._update_actions()
        if self._selected_backend() == "ollama-cloud":
            self._discover_ollama_models()
        self._refresh_from_frame()

    def _selected_backend(self) -> str:
        return self.view.settings_page.selected_backend()

    def _settings_provider_changed(self, backend: str) -> None:
        self._update_actions()
        if backend == "ollama-cloud":
            self._discover_ollama_models()

    def _settings_applied(self) -> None:
        self._refresh_backend_label()
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
        self.request_progress.stop()
        self.model_discovery.close()
        if self._task is not None:
            self._task.cancel()

    def _clear_transcript(self) -> None:
        if self._task is None:
            self.conversation.reset()

    def _analysis_stream(self, chunk: str) -> None:
        if self._alive and self.conversation.stream(chunk):
            self.view.status_label.setText("Receiving response...")

    def _refresh_backend_label(self, config: Optional[RuntimeConfig] = None) -> None:
        active = config or get_runtime_config()
        model = active.provider.model or "default model"
        effort = active.provider.reasoning_effort or "default effort"
        backend = BACKEND_LABELS.get(active.provider.backend, active.provider.backend)
        summary = f"{backend}  ·  {model}  ·  {effort}"
        self.view.backend_label.setText(summary)
        self.view.backend_label.setToolTip(summary)

    def _refresh_from_frame(self) -> None:
        if self.frame is None:
            self._set_current_function(None)
            return
        try:
            view = self.frame.getCurrentViewInterface()
            if view is None:
                self._set_current_function(None)
                return
            data = view.getData()
            if data is not None:
                self.bv = data
            self._set_function_for_offset(view.getCurrentOffset())
        except Exception:
            self._set_current_function(None)

    def _set_function_for_offset(self, offset: int) -> None:
        if self.bv is None:
            self._set_current_function(None)
            return
        functions = self.bv.get_functions_containing(offset)
        self._set_current_function(functions[0] if functions else None)

    def _set_current_function(self, function: Optional[Function]) -> None:
        self._current_function = function
        if function is None:
            self.view.context_name.setText("No function selected")
            self.view.context_detail.setText(
                "Move the cursor into a function to begin."
            )
        else:
            self.view.context_name.setText(function.name)
            architecture = (
                self.bv.arch.name
                if self.bv is not None and self.bv.arch is not None
                else "unknown architecture"
            )
            self.view.context_detail.setText(
                f"0x{function.start:x}  |  {architecture}  |  current function HLIL"
            )
        self._update_actions()

    def _update_actions(self, *_args: object) -> None:
        ready = self._current_function is not None and self._task is None
        self.view.explain_button.setEnabled(ready)
        self.view.ask_button.setEnabled(
            ready and bool(self.view.prompt.toPlainText().strip())
        )
        self.view.stop_button.setEnabled(self._task is not None)
        self.view.clear_button.setEnabled(self._task is None)
        self.view.settings_page.set_busy(
            self._task is not None,
            self.model_discovery.busy,
        )

    def _explain(self) -> None:
        self._start_request(DEFAULT_QUESTION, "Explain this function.")

    def _ask(self) -> None:
        question = self.view.prompt.toPlainText().strip()
        if question:
            self._start_request(question, question)

    def _start_request(self, question: str, display_question: str) -> None:
        if self._task is not None or self._current_function is None or self.bv is None:
            return

        self._save_selection()
        config = get_runtime_config()
        function = self._current_function
        self.conversation.append("You", display_question, function.name)
        backend = BACKEND_LABELS.get(config.provider.backend, config.provider.backend)
        model = config.provider.model or "default model"
        effort = config.provider.reasoning_effort or "default effort"
        self.conversation.start_response(
            f"{function.name}  ·  {backend}  ·  {model}  ·  {effort}"
        )
        self.view.prompt.clear()
        self._refresh_backend_label(config)
        self.request_progress.begin(f"Preparing {function.name} with {backend}...")

        self._task = AnalyzeFunctionTask(
            self.bv,
            function,
            question,
            config,
            show_report=False,
            on_complete=self._analysis_complete,
            on_error=self._analysis_error,
            on_cancelled=self._analysis_cancelled,
            on_progress=self.request_progress.update,
            on_stream=self._analysis_stream,
        )
        self._update_actions()
        self._task.start()

    def _cancel(self) -> None:
        if self._task is None:
            return
        self.view.status_label.setText("Cancelling request...")
        self.view.stop_button.setEnabled(False)
        self._task.cancel()

    def _analysis_complete(
        self,
        context: FunctionContext,
        result: ProviderResult,
    ) -> None:
        if not self._alive:
            return
        model = result.model or "default model"
        effort = result.reasoning_effort or "default effort"
        backend = BACKEND_LABELS.get(result.backend, result.backend)
        self.conversation.complete(
            result.text,
            f"{context.function_name}  ·  {backend}  ·  {model}  ·  {effort}",
        )
        self._task = None
        self.request_progress.finish("Complete", completed=True)
        self._update_actions()

    def _analysis_error(self, message: str) -> None:
        if not self._alive:
            return
        self.conversation.fail(message)
        self._task = None
        self.request_progress.finish("Request failed. Check the message above.")
        self._update_actions()

    def _analysis_cancelled(self) -> None:
        if not self._alive:
            return
        self.conversation.cancel()
        self._task = None
        self.request_progress.finish("Request cancelled")
        self._update_actions()

    def notifyOffsetChanged(self, offset: int) -> None:
        self._set_function_for_offset(offset)

    def notifyViewChanged(self, view_frame: Optional[ViewFrame]) -> None:
        self.frame = view_frame
        self._refresh_from_frame()


class AxioAnalystSidebarType(SidebarWidgetType):
    def __init__(self):
        icon = QtGui.QImage(56, 56, QtGui.QImage.Format.Format_ARGB32)
        icon.fill(0)
        painter = QtGui.QPainter(icon)
        painter.setFont(QtGui.QFont("Open Sans", 28, QtGui.QFont.Weight.DemiBold))
        painter.setPen(QtGui.QColor(255, 255, 255, 255))
        painter.drawText(
            QtCore.QRectF(0, 0, 56, 56),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            "AX",
        )
        painter.end()
        SidebarWidgetType.__init__(self, icon, WIDGET_NAME)

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

"""Native Binary Ninja sidebar for Axio Analyst."""

import threading
from dataclasses import dataclass
from typing import Optional

from binaryninja import BinaryView, Function
from binaryninja.mainthread import execute_on_main_thread
from binaryninjaui import (
    Sidebar,
    SidebarWidget,
    SidebarWidgetLocation,
    SidebarWidgetType,
    UIContext,
    ViewFrame,
)
from PySide6 import QtCore, QtGui, QtWidgets

from .models import FunctionContext, ProviderError, ProviderResult
from .prompts import DEFAULT_QUESTION
from .providers import (
    fetch_ollama_cloud_catalog,
    parse_ollama_cloud_models,
)
from .rendering import restored_scroll_value, safe_markdown
from .settings import BACKEND_LABELS, RuntimeConfig, get_runtime_config
from .settings_page import SettingsPage
from .task import AnalyzeFunctionTask

WIDGET_NAME = "Axio Analyst"


@dataclass
class ChatMessage:
    role: str
    body: str
    meta: str = ""


class PromptEdit(QtWidgets.QPlainTextEdit):
    submitRequested = QtCore.Signal()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        submit_keys = (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter)
        control = QtCore.Qt.KeyboardModifier.ControlModifier
        if event.key() in submit_keys and event.modifiers() & control:
            self.submitRequested.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class AxioAnalystSidebar(SidebarWidget):
    """Conversation surface scoped to the function under the cursor."""

    def __init__(self, name: str, frame: ViewFrame, data: BinaryView):
        SidebarWidget.__init__(self, name)
        self.m_actionHandler.setupActionHandler(self)

        self.frame: Optional[ViewFrame] = frame
        self.bv: Optional[BinaryView] = data
        self._current_function: Optional[Function] = None
        self._task: Optional[AnalyzeFunctionTask] = None
        self._ollama_catalog_loading = False
        self._ollama_discovery_process: Optional[QtCore.QProcess] = None
        self._messages: list[ChatMessage] = []
        self._active_message_index: Optional[int] = None
        self._request_clock = QtCore.QElapsedTimer()
        self._elapsed_timer = QtCore.QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._progress_generation = 0
        self._alive = True

        self._build_interface()
        self.destroyed.connect(self._mark_dead)
        self._refresh_from_frame()

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout()
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Axio Analyst")
        title_font = title.font()
        title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        title_font.setPointSizeF(title_font.pointSizeF() + 1.0)
        title.setFont(title_font)
        title.setMinimumWidth(110)
        header.addWidget(title)
        header.addStretch(1)

        self.chat_tab_button = QtWidgets.QToolButton()
        self.chat_tab_button.setText("Chat")
        self.chat_tab_button.setCheckable(True)
        self.chat_tab_button.setAccessibleName("Show conversation")
        self.settings_tab_button = QtWidgets.QToolButton()
        self.settings_tab_button.setText("Settings")
        self.settings_tab_button.setCheckable(True)
        self.settings_tab_button.setAccessibleName("Show Axio Analyst settings")
        self.page_buttons = QtWidgets.QButtonGroup(self)
        self.page_buttons.setExclusive(True)
        self.page_buttons.addButton(self.chat_tab_button)
        self.page_buttons.addButton(self.settings_tab_button)
        header.addWidget(self.chat_tab_button)
        header.addWidget(self.settings_tab_button)
        root.addLayout(header)

        self.pages = QtWidgets.QStackedWidget()
        root.addWidget(self.pages, 1)

        chat_page = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(8)

        context_frame = QtWidgets.QFrame()
        context_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        context_layout = QtWidgets.QVBoxLayout(context_frame)
        context_layout.setContentsMargins(9, 7, 9, 7)
        context_layout.setSpacing(2)

        self.context_name = QtWidgets.QLabel("No function selected")
        name_font = self.context_name.font()
        name_font.setWeight(QtGui.QFont.Weight.DemiBold)
        self.context_name.setFont(name_font)
        self.context_name.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.context_detail = QtWidgets.QLabel(
            "Move the cursor into a function to begin."
        )
        self.context_detail.setWordWrap(True)
        detail_font = self.context_detail.font()
        detail_font.setPointSizeF(max(8.0, detail_font.pointSizeF() - 1.0))
        self.context_detail.setFont(detail_font)

        context_layout.addWidget(self.context_name)
        context_layout.addWidget(self.context_detail)
        chat_layout.addWidget(context_frame)

        transcript_header = QtWidgets.QHBoxLayout()
        self.backend_label = QtWidgets.QLabel()
        self.backend_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.backend_label.setWordWrap(True)
        backend_font = self.backend_label.font()
        backend_font.setPointSizeF(max(8.0, backend_font.pointSizeF() - 1.0))
        self.backend_label.setFont(backend_font)
        self.clear_button = QtWidgets.QToolButton()
        self.clear_button.setText("Clear")
        self.clear_button.setToolTip("Clear this sidebar's conversation")
        self.clear_button.setAccessibleName("Clear conversation")
        self.clear_button.clicked.connect(self._clear_transcript)
        conversation_label = QtWidgets.QLabel("Conversation")
        conversation_font = conversation_label.font()
        conversation_font.setWeight(QtGui.QFont.Weight.DemiBold)
        conversation_label.setFont(conversation_font)
        transcript_header.addWidget(conversation_label)
        transcript_header.addStretch(1)
        transcript_header.addWidget(self.clear_button)
        chat_layout.addLayout(transcript_header)
        chat_layout.addWidget(self.backend_label)

        self.transcript = QtWidgets.QTextBrowser()
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setUndoRedoEnabled(False)
        self.transcript.setAccessibleName("Axio Analyst conversation")
        self.transcript.document().setDocumentMargin(8)
        palette = self.transcript.palette()
        code_background = palette.color(QtGui.QPalette.ColorRole.AlternateBase).name()
        border_color = palette.color(QtGui.QPalette.ColorRole.Mid).name()
        self.transcript.document().setDefaultStyleSheet(
            "pre { margin: 8px 0; padding: 7px; background-color: "
            f"{code_background}; border: 1px solid {border_color}; }} "
            "code { font-family: monospace; } "
            "h1, h2, h3 { margin-top: 12px; margin-bottom: 5px; } "
            "p { margin-top: 3px; margin-bottom: 7px; }"
        )
        chat_layout.addWidget(self.transcript, 1)

        prompt_label = QtWidgets.QLabel("Ask about the current function")
        prompt_font = prompt_label.font()
        prompt_font.setWeight(QtGui.QFont.Weight.DemiBold)
        prompt_label.setFont(prompt_font)
        chat_layout.addWidget(prompt_label)

        self.prompt = PromptEdit()
        self.prompt.setPlaceholderText(
            "Trace a value, recover an algorithm, or explain behavior..."
        )
        self.prompt.setAccessibleName("Question about current function")
        self.prompt.setMinimumHeight(72)
        self.prompt.setMaximumHeight(128)
        self.prompt.setTabChangesFocus(True)
        self.prompt.textChanged.connect(self._update_actions)
        self.prompt.submitRequested.connect(self._ask)
        chat_layout.addWidget(self.prompt)

        actions = QtWidgets.QHBoxLayout()
        self.explain_button = QtWidgets.QPushButton("Explain")
        self.explain_button.setToolTip("Explain the current function")
        self.explain_button.clicked.connect(self._explain)
        self.ask_button = QtWidgets.QPushButton("Ask")
        self.ask_button.setToolTip("Send question (Ctrl+Enter)")
        self.ask_button.setDefault(True)
        self.ask_button.clicked.connect(self._ask)
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setToolTip("Cancel the active request")
        self.stop_button.clicked.connect(self._cancel)
        actions.addWidget(self.explain_button)
        actions.addWidget(self.ask_button, 1)
        actions.addWidget(self.stop_button)
        chat_layout.addLayout(actions)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(5)
        self.progress_bar.setAccessibleName("Request progress")
        self.progress_bar.hide()
        chat_layout.addWidget(self.progress_bar)

        status_row = QtWidgets.QHBoxLayout()
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Request status")
        self.elapsed_label = QtWidgets.QLabel()
        self.elapsed_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.elapsed_label.setAccessibleName("Request elapsed time")
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.elapsed_label)
        chat_layout.addLayout(status_row)

        self.disclosure = QtWidgets.QLabel(
            "Only this function's address-labelled HLIL is sent when you ask."
        )
        self.disclosure.setWordWrap(True)
        disclosure_font = self.disclosure.font()
        disclosure_font.setPointSizeF(max(8.0, disclosure_font.pointSizeF() - 1.0))
        self.disclosure.setFont(disclosure_font)
        chat_layout.addWidget(self.disclosure)

        self.settings_page = SettingsPage()
        self.pages.addWidget(chat_page)
        self.pages.addWidget(self.settings_page)

        self.setLayout(root)
        self.chat_tab_button.clicked.connect(self._show_chat)
        self.settings_tab_button.clicked.connect(self._show_settings)
        self.settings_page.providerChanged.connect(self._settings_provider_changed)
        self.settings_page.applied.connect(self._settings_applied)
        self.settings_page.refreshModelsRequested.connect(
            self._discover_ollama_models
        )
        self.setTabOrder(self.chat_tab_button, self.settings_tab_button)
        self.setTabOrder(self.settings_tab_button, self.prompt)
        self.setTabOrder(self.prompt, self.ask_button)
        self.setTabOrder(self.ask_button, self.explain_button)
        self.setTabOrder(self.explain_button, self.stop_button)
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)
        self._clear_transcript()
        self._refresh_backend_label()
        self._update_actions()
        if self._selected_backend() == "ollama-cloud":
            self._discover_ollama_models()

    def _selected_backend(self) -> str:
        return self.settings_page.selected_backend()

    def _selected_model(self) -> str:
        return self.settings_page.selected_model()

    def _selected_effort(self) -> str:
        return self.settings_page.selected_effort()

    def _show_chat(self, *_args: object) -> None:
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)
        self.prompt.setFocus()

    def _show_settings(self, *_args: object) -> None:
        self.settings_tab_button.setChecked(True)
        self.pages.setCurrentIndex(1)

    def _settings_provider_changed(self, backend: str) -> None:
        self._update_actions()
        if backend == "ollama-cloud":
            self._discover_ollama_models()

    def _settings_applied(self) -> None:
        self._refresh_backend_label()
        self._update_actions()

    def _save_selection(self, *_args: object) -> None:
        self.settings_page.save_selection()
        self._refresh_backend_label()

    def _discover_ollama_models(self, *_args: object) -> None:
        if self._selected_backend() != "ollama-cloud":
            return
        if self._ollama_catalog_loading:
            return
        if (
            self._ollama_discovery_process is not None
            and self._ollama_discovery_process.state()
            != QtCore.QProcess.ProcessState.NotRunning
        ):
            return

        self._save_selection()
        self._ollama_catalog_loading = True
        self.settings_page.set_status("Fetching available Ollama Cloud models...")
        self._update_actions()
        threading.Thread(
            target=self._fetch_ollama_catalog,
            name="AxioAnalyst-OllamaCatalog",
            daemon=True,
        ).start()

    def _fetch_ollama_catalog(self) -> None:
        models: list[str] = []
        error_detail = ""
        try:
            models = fetch_ollama_cloud_catalog()
        except ProviderError as exc:
            error_detail = str(exc)

        def finish() -> None:
            self._ollama_catalog_finished(models, error_detail)

        try:
            execute_on_main_thread(finish)
        except Exception:
            pass

    def _ollama_catalog_finished(
        self,
        models: list[str],
        error_detail: str,
    ) -> None:
        if not self._alive:
            return
        self._ollama_catalog_loading = False

        if self._selected_backend() != "ollama-cloud":
            self._update_actions()
            return
        if error_detail:
            self.settings_page.set_status(
                "Remote Ollama catalog unavailable; checking registered models..."
            )
            self._discover_registered_ollama_models(error_detail)
            return

        if not models:
            self._discover_registered_ollama_models(
                "the remote catalog contained no models"
            )
            return

        self._replace_ollama_models(models)
        self.settings_page.set_status(
            f"Found {len(models)} available Ollama Cloud model(s)"
        )
        self._update_actions()

    def _discover_registered_ollama_models(self, remote_error: str = "") -> None:
        executable = self.settings_page.selected_ollama_executable()
        process = QtCore.QProcess(self)
        process.setProgram(executable)
        process.setArguments(["list"])
        process.setProcessChannelMode(QtCore.QProcess.ProcessChannelMode.SeparateChannels)
        process.finished.connect(self._ollama_discovery_finished)
        process.errorOccurred.connect(self._ollama_discovery_error)
        process.setProperty("remoteError", remote_error)
        self._ollama_discovery_process = process
        self.settings_page.set_status("Checking registered Ollama Cloud models...")
        self._update_actions()
        process.start()

    def _ollama_discovery_finished(
        self,
        exit_code: int,
        *_args: object,
    ) -> None:
        process = self._ollama_discovery_process
        if process is None:
            return
        stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        self._ollama_discovery_process = None
        process.deleteLater()

        if self._selected_backend() != "ollama-cloud":
            self._update_actions()
            return
        if exit_code != 0:
            detail = stderr.strip() or f"ollama list exited with code {exit_code}"
            self.settings_page.set_status(
                f"Could not refresh Ollama models: {detail}"
            )
            self._update_actions()
            return

        models = parse_ollama_cloud_models(stdout)
        self._replace_ollama_models(models)
        if models:
            self.settings_page.set_status(
                f"Remote catalog unavailable; found {len(models)} registered "
                "Ollama Cloud model(s)"
            )
        else:
            remote_error = str(process.property("remoteError") or "unknown error")
            self.settings_page.set_status(
                "Could not discover Ollama Cloud models. "
                f"Remote: {remote_error}. Type a model name directly."
            )
        self._update_actions()

    def _ollama_discovery_error(self, *_args: object) -> None:
        process = self._ollama_discovery_process
        if process is None:
            return
        detail = process.errorString()
        self._ollama_discovery_process = None
        process.deleteLater()
        if self._selected_backend() == "ollama-cloud":
            self.settings_page.set_status(
                f"Could not start Ollama model discovery: {detail}"
            )
        self._update_actions()

    def _replace_ollama_models(self, models: list[str]) -> None:
        self.settings_page.replace_ollama_models(models)

    def _mark_dead(self, *_args: object) -> None:
        self._alive = False
        self._elapsed_timer.stop()
        if self._task is not None:
            self._task.cancel()

    def _clear_transcript(self) -> None:
        if self._task is not None:
            return
        self._messages = [
            ChatMessage(
                "Axio Analyst",
                "Select a function, ask a question, or use **Explain** for a quick read.",
            )
        ]
        self._active_message_index = None
        self._render_transcript(force_bottom=True)

    def _append_message(self, role: str, body: str, meta: str = "") -> int:
        self._messages.append(ChatMessage(role, body, meta))
        self._render_transcript(force_bottom=True)
        return len(self._messages) - 1

    def _render_transcript(self, force_bottom: bool = False) -> None:
        scrollbar = self.transcript.verticalScrollBar()
        previous_value = scrollbar.value()
        previous_maximum = scrollbar.maximum()
        self.transcript.clear()
        cursor = self.transcript.textCursor()
        palette = self.transcript.palette()
        header = QtGui.QTextCharFormat()
        header.setFontWeight(QtGui.QFont.Weight.DemiBold)
        header.setForeground(palette.color(QtGui.QPalette.ColorRole.Link))
        meta_format = QtGui.QTextCharFormat()
        meta_format.setForeground(
            palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        )

        for index, message in enumerate(self._messages):
            if index:
                separator = QtGui.QTextBlockFormat()
                separator.setTopMargin(8)
                cursor.insertBlock(separator)
            cursor.insertText(message.role, header)
            if message.meta:
                cursor.insertText(f"  ·  {message.meta}", meta_format)
            cursor.insertBlock()
            body = message.body or "_Receiving response..._"
            cursor.insertMarkdown(safe_markdown(body.strip()))
            cursor.insertBlock()

        self.transcript.setTextCursor(cursor)
        scrollbar.setValue(
            restored_scroll_value(
                previous_value,
                previous_maximum,
                scrollbar.maximum(),
                force_bottom,
            )
        )

    def _analysis_stream(self, chunk: str) -> None:
        if not self._alive or self._active_message_index is None or not chunk:
            return
        if self._active_message_index >= len(self._messages):
            return
        self._messages[self._active_message_index].body += chunk
        self._render_transcript()
        self.status_label.setText("Receiving response...")

    def _refresh_backend_label(self, config: Optional[RuntimeConfig] = None) -> None:
        active = config or get_runtime_config()
        model = active.provider.model or "default model"
        effort = active.provider.reasoning_effort or "default effort"
        backend = BACKEND_LABELS.get(active.provider.backend, active.provider.backend)
        summary = f"{backend}  ·  {model}  ·  {effort}"
        self.backend_label.setText(summary)
        self.backend_label.setToolTip(summary)

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
            self.context_name.setText("No function selected")
            self.context_detail.setText("Move the cursor into a function to begin.")
        else:
            self.context_name.setText(function.name)
            architecture = (
                self.bv.arch.name
                if self.bv is not None and self.bv.arch is not None
                else "unknown architecture"
            )
            self.context_detail.setText(
                f"0x{function.start:x}  |  {architecture}  |  current function HLIL"
            )
        self._update_actions()

    def _update_actions(self) -> None:
        ready = self._current_function is not None and self._task is None
        self.explain_button.setEnabled(ready)
        self.ask_button.setEnabled(ready and bool(self.prompt.toPlainText().strip()))
        self.stop_button.setEnabled(self._task is not None)
        self.clear_button.setEnabled(self._task is None)
        discovering = (
            self._ollama_catalog_loading
            or (
                self._ollama_discovery_process is not None
                and self._ollama_discovery_process.state()
                != QtCore.QProcess.ProcessState.NotRunning
            )
        )
        self.settings_page.set_busy(self._task is not None, discovering)

    def _begin_progress(self, message: str) -> None:
        self._progress_generation += 1
        self._request_clock.start()
        self._elapsed_timer.start()
        self.elapsed_label.setText("0s")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(5)
        self.progress_bar.show()
        self.status_label.setText(message)

    def _analysis_progress(self, message: str, value: int) -> None:
        if not self._alive or self._task is None:
            return
        self.progress_bar.show()
        if value == 40:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _update_elapsed(self) -> None:
        if not self._request_clock.isValid():
            return
        elapsed_seconds = self._request_clock.elapsed() // 1000
        if elapsed_seconds < 60:
            self.elapsed_label.setText(f"{elapsed_seconds}s")
        else:
            minutes, seconds = divmod(elapsed_seconds, 60)
            self.elapsed_label.setText(f"{minutes}m {seconds:02d}s")

    def _finish_progress(self, message: str, completed: bool = False) -> None:
        self._elapsed_timer.stop()
        self._update_elapsed()
        self.status_label.setText(message)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if completed else 0)
        generation = self._progress_generation
        QtCore.QTimer.singleShot(
            1200,
            lambda: self._hide_progress(generation),
        )

    def _hide_progress(self, generation: int) -> None:
        if generation == self._progress_generation and self._task is None:
            self.progress_bar.hide()

    def _explain(self) -> None:
        self._start_request(DEFAULT_QUESTION, "Explain this function.")

    def _ask(self) -> None:
        question = self.prompt.toPlainText().strip()
        if not question:
            return
        self._start_request(question, question)

    def _start_request(self, question: str, display_question: str) -> None:
        if self._task is not None or self._current_function is None or self.bv is None:
            return

        self._save_selection()
        config = get_runtime_config()
        function = self._current_function
        self._append_message("You", display_question, function.name)
        backend = BACKEND_LABELS.get(
            config.provider.backend,
            config.provider.backend,
        )
        model = config.provider.model or "default model"
        effort = config.provider.reasoning_effort or "default effort"
        self._active_message_index = self._append_message(
            "Axio Analyst",
            "",
            f"{function.name}  ·  {backend}  ·  {model}  ·  {effort}",
        )
        self.prompt.clear()
        self._refresh_backend_label(config)
        self._begin_progress(f"Preparing {function.name} with {backend}...")

        self._task = AnalyzeFunctionTask(
            self.bv,
            function,
            question,
            config,
            show_report=False,
            on_complete=self._analysis_complete,
            on_error=self._analysis_error,
            on_cancelled=self._analysis_cancelled,
            on_progress=self._analysis_progress,
            on_stream=self._analysis_stream,
        )
        self._update_actions()
        self._task.start()

    def _cancel(self) -> None:
        if self._task is None:
            return
        self.status_label.setText("Cancelling request...")
        self.stop_button.setEnabled(False)
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
        if self._active_message_index is None:
            self._active_message_index = self._append_message(
                "Axio Analyst",
                result.text,
            )
        else:
            message = self._messages[self._active_message_index]
            message.body = result.text
            message.meta = (
                f"{context.function_name}  ·  {backend}  ·  {model}  ·  {effort}"
            )
            self._render_transcript(force_bottom=True)
        self._active_message_index = None
        self._task = None
        self._finish_progress("Complete", completed=True)
        self._update_actions()

    def _analysis_error(self, message: str) -> None:
        if not self._alive:
            return
        if self._active_message_index is not None:
            active = self._messages[self._active_message_index]
            if active.body:
                active.body += f"\n\n---\n\n**Request failed:** {message}"
            else:
                active.role = "Request failed"
                active.body = message
            self._render_transcript(force_bottom=True)
        else:
            self._append_message("Request failed", message)
        self._active_message_index = None
        self._task = None
        self._finish_progress("Request failed. Check the message above.")
        self._update_actions()

    def _analysis_cancelled(self) -> None:
        if not self._alive:
            return
        if self._active_message_index is not None:
            active = self._messages[self._active_message_index]
            if not active.body:
                active.body = "_Request cancelled before a response was received._"
            else:
                active.body += "\n\n_Request cancelled._"
            self._render_transcript(force_bottom=True)
        self._active_message_index = None
        self._task = None
        self._finish_progress("Request cancelled")
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

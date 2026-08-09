"""Widget construction for the Axio Analyst sidebar."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import ContextOptions
from ..core.version import VERSION
from .settings_page import SettingsPage


TIGHT_SPACING = 4
ROW_SPACING = 8
SECTION_SPACING = 12


class ElidingLabel(QtWidgets.QLabel):
    """Single-line label that preserves its full value in a tooltip."""

    def __init__(self, text: str = "", parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._full_text = ""
        self._detail_tooltip = ""
        self.setMinimumWidth(0)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.setText(text)

    def set_detail_tooltip(self, text: str) -> None:
        self._detail_tooltip = text
        self._refresh_text()

    def setText(self, text: str) -> None:
        self._full_text = text
        self._refresh_text()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._refresh_text()

    def _refresh_text(self) -> None:
        width = max(0, self.contentsRect().width())
        rendered = self.fontMetrics().elidedText(
            self._full_text,
            QtCore.Qt.TextElideMode.ElideRight,
            width,
        )
        QtWidgets.QLabel.setText(self, rendered)
        self.setToolTip(
            self._detail_tooltip
            or (self._full_text if rendered != self._full_text else "")
        )


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


class SidebarView(QtWidgets.QWidget):
    askRequested = QtCore.Signal()
    clearRequested = QtCore.Signal()
    explainRequested = QtCore.Signal()
    exportRequested = QtCore.Signal()
    contextOptionsChanged = QtCore.Signal()
    previewRequested = QtCore.Signal()
    stopRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._build_interface()

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(ROW_SPACING)

        header = QtWidgets.QHBoxLayout()
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
        header.addStretch(1)
        self.version_label = QtWidgets.QLabel(f"v{VERSION}")
        self.version_label.setAccessibleName(f"Axio Analyst version {VERSION}")
        self.version_label.setToolTip(f"Axio Analyst version {VERSION}")
        version_font = self.version_label.font()
        version_font.setPointSizeF(max(8.0, version_font.pointSizeF() - 1.0))
        self.version_label.setFont(version_font)
        header.addWidget(self.version_label)
        root.addLayout(header)

        self.pages = QtWidgets.QStackedWidget()
        root.addWidget(self.pages, 1)

        chat_page = QtWidgets.QWidget()
        chat_layout = QtWidgets.QVBoxLayout(chat_page)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(ROW_SPACING)

        context_frame = QtWidgets.QFrame()
        context_frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        context_layout = QtWidgets.QVBoxLayout(context_frame)
        context_layout.setContentsMargins(8, 6, 8, 6)
        context_layout.setSpacing(TIGHT_SPACING)

        context_header = QtWidgets.QHBoxLayout()
        context_header.setSpacing(ROW_SPACING)
        self.context_name = ElidingLabel("No function selected")
        name_font = self.context_name.font()
        name_font.setWeight(QtGui.QFont.Weight.DemiBold)
        self.context_name.setFont(name_font)
        self.context_button = QtWidgets.QToolButton()
        self.context_button.setText("Context")
        self.context_button.setToolTip("Choose and preview the exact request context")
        context_header.addWidget(self.context_name, 1)
        context_header.addWidget(self.context_button)
        context_layout.addLayout(context_header)

        context_meta = QtWidgets.QHBoxLayout()
        context_meta.setSpacing(ROW_SPACING)
        self.context_detail = ElidingLabel(
            "Move the cursor into a function to begin."
        )
        detail_font = self.context_detail.font()
        detail_font.setPointSizeF(max(8.0, detail_font.pointSizeF() - 1.0))
        self.context_detail.setFont(detail_font)
        self.context_summary = QtWidgets.QLabel("Not previewed")
        self.context_summary.setAccessibleName("Context snapshot summary")
        self.context_summary.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Maximum,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        summary_font = self.context_summary.font()
        summary_font.setPointSizeF(max(8.0, summary_font.pointSizeF() - 1.0))
        self.context_summary.setFont(summary_font)
        context_meta.addWidget(self.context_detail, 1)
        context_meta.addWidget(self.context_summary)
        context_layout.addLayout(context_meta)
        chat_layout.addWidget(context_frame)

        transcript_header = QtWidgets.QHBoxLayout()
        transcript_header.setSpacing(ROW_SPACING)
        conversation_label = QtWidgets.QLabel("Conversation")
        conversation_font = conversation_label.font()
        conversation_font.setWeight(QtGui.QFont.Weight.DemiBold)
        conversation_label.setFont(conversation_font)
        self.backend_label = ElidingLabel()
        backend_font = self.backend_label.font()
        backend_font.setPointSizeF(max(8.0, backend_font.pointSizeF() - 1.0))
        self.backend_label.setFont(backend_font)
        self.clear_button = QtWidgets.QToolButton()
        self.clear_button.setText("Clear")
        self.clear_button.setToolTip("Clear this sidebar's conversation")
        self.clear_button.setAccessibleName("Clear conversation")
        self.export_button = QtWidgets.QToolButton()
        self.export_button.setText("Export")
        self.export_button.setToolTip("Export this conversation as Markdown")
        self.export_button.setAccessibleName("Export conversation")
        transcript_header.addWidget(conversation_label)
        transcript_header.addWidget(self.backend_label, 1)
        transcript_header.addWidget(self.export_button)
        transcript_header.addWidget(self.clear_button)
        chat_layout.addLayout(transcript_header)

        self.transcript = QtWidgets.QTextBrowser()
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setUndoRedoEnabled(False)
        self.transcript.setAccessibleName("Axio Analyst conversation")
        self.transcript.setMinimumHeight(160)
        self.transcript.document().setDocumentMargin(8)
        palette = self.transcript.palette()
        code_background = palette.color(
            QtGui.QPalette.ColorRole.AlternateBase
        ).name()
        border_color = palette.color(QtGui.QPalette.ColorRole.Mid).name()
        self.transcript.document().setDefaultStyleSheet(
            "pre { margin: 8px 0; padding: 8px; background-color: "
            f"{code_background}; border: 1px solid {border_color}; }} "
            "code { font-family: monospace; } "
            "h1, h2, h3 { margin-top: 12px; margin-bottom: 4px; } "
            "p { margin-top: 4px; margin-bottom: 8px; }"
        )
        chat_layout.addWidget(self.transcript, 1)

        composer = QtWidgets.QFrame()
        composer.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        composer_layout = QtWidgets.QVBoxLayout(composer)
        composer_layout.setContentsMargins(8, 6, 8, 6)
        composer_layout.setSpacing(TIGHT_SPACING)

        prompt_header = QtWidgets.QHBoxLayout()
        prompt_header.setSpacing(ROW_SPACING)
        prompt_label = QtWidgets.QLabel("Ask a question")
        prompt_font = prompt_label.font()
        prompt_font.setWeight(QtGui.QFont.Weight.DemiBold)
        prompt_label.setFont(prompt_font)
        shortcut_label = QtWidgets.QLabel("Ctrl+Enter to send")
        shortcut_font = shortcut_label.font()
        shortcut_font.setPointSizeF(max(8.0, shortcut_font.pointSizeF() - 1.0))
        shortcut_label.setFont(shortcut_font)
        self.compare_toggle = QtWidgets.QToolButton()
        self.compare_toggle.setText("Compare")
        self.compare_toggle.setCheckable(True)
        self.compare_toggle.setToolTip("Compare the response with a second provider")
        prompt_header.addWidget(prompt_label)
        prompt_header.addStretch(1)
        prompt_header.addWidget(shortcut_label)
        prompt_header.addWidget(self.compare_toggle)
        composer_layout.addLayout(prompt_header)

        self.prompt = PromptEdit()
        self.prompt.setPlaceholderText(
            "Trace a value, recover an algorithm, or explain behavior..."
        )
        self.prompt.setAccessibleName("Question about current function")
        prompt_height = max(52, self.prompt.fontMetrics().lineSpacing() * 3 + 12)
        self.prompt.setFixedHeight(prompt_height)
        self.prompt.setTabChangesFocus(True)
        composer_layout.addWidget(self.prompt)

        self.comparison_panel = QtWidgets.QWidget()
        compare_row = QtWidgets.QHBoxLayout(self.comparison_panel)
        compare_row.setContentsMargins(0, 0, 0, 0)
        compare_row.setSpacing(ROW_SPACING)
        compare_label = QtWidgets.QLabel("Second provider")
        self.compare_combo = QtWidgets.QComboBox()
        self.compare_combo.setAccessibleName("Optional comparison provider")
        self.compare_combo.addItem("No comparison", "")
        self.compare_combo.addItem("Claude Code", "claude-code")
        self.compare_combo.addItem("Codex", "codex-cli")
        self.compare_combo.addItem("Ollama Cloud", "ollama-cloud")
        compare_row.addWidget(compare_label)
        compare_row.addWidget(self.compare_combo, 1)
        self.comparison_panel.hide()
        composer_layout.addWidget(self.comparison_panel)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(ROW_SPACING)
        self.explain_button = QtWidgets.QPushButton("Explain function")
        self.explain_button.setToolTip("Explain the current function")
        self.ask_button = QtWidgets.QPushButton("Ask")
        self.ask_button.setToolTip("Send question (Ctrl+Enter)")
        self.ask_button.setDefault(True)
        self.stop_button = QtWidgets.QPushButton("Stop request")
        self.stop_button.setToolTip("Cancel the active request")
        self.submit_action = QtWidgets.QStackedWidget()
        self.submit_action.addWidget(self.ask_button)
        self.submit_action.addWidget(self.stop_button)
        self.submit_action.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        actions.addWidget(self.explain_button)
        actions.addWidget(self.submit_action, 1)
        composer_layout.addLayout(actions)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximumHeight(4)
        self.progress_bar.setAccessibleName("Request progress")
        self.progress_bar.hide()
        composer_layout.addWidget(self.progress_bar)

        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(ROW_SPACING)
        self.status_label = ElidingLabel("Ready")
        self.status_label.setAccessibleName("Request status")
        self.elapsed_label = QtWidgets.QLabel()
        self.elapsed_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.elapsed_label.setAccessibleName("Request elapsed time")
        status_row.addWidget(self.status_label, 1)
        status_row.addWidget(self.elapsed_label)
        composer_layout.addLayout(status_row)

        self.disclosure = ElidingLabel(
            "Scope: current function · extra context is opt-in"
        )
        self.disclosure.setAccessibleName("Request context disclosure")
        self.disclosure.set_detail_tooltip(
            "The primary function is included by default. Only visibly enabled, "
            "bounded context packs are added when you ask."
        )
        disclosure_font = self.disclosure.font()
        disclosure_font.setPointSizeF(
            max(8.0, disclosure_font.pointSizeF() - 1.0)
        )
        self.disclosure.setFont(disclosure_font)
        composer_layout.addWidget(self.disclosure)
        chat_layout.addWidget(composer)

        context_page = QtWidgets.QWidget()
        context_page_layout = QtWidgets.QVBoxLayout(context_page)
        context_page_layout.setContentsMargins(0, 0, 0, 0)
        context_page_layout.setSpacing(SECTION_SPACING)

        context_page_header = QtWidgets.QHBoxLayout()
        context_title = QtWidgets.QLabel("Request context")
        context_title_font = context_title.font()
        context_title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        context_title.setFont(context_title_font)
        self.context_back_button = QtWidgets.QToolButton()
        self.context_back_button.setText("Back to chat")
        context_page_header.addWidget(context_title)
        context_page_header.addStretch(1)
        context_page_header.addWidget(self.context_back_button)
        context_page_layout.addLayout(context_page_header)

        context_note = QtWidgets.QLabel(
            "The current function is always included. Add only the nearby "
            "evidence this request needs."
        )
        context_note.setWordWrap(True)
        context_page_layout.addWidget(context_note)

        options_group = QtWidgets.QGroupBox("Optional context packs")
        options_layout = QtWidgets.QVBoxLayout(options_group)
        options_layout.setSpacing(TIGHT_SPACING)
        self.selection_context = QtWidgets.QCheckBox("Current selection")
        self.callers_context = QtWidgets.QCheckBox("Direct callers (3)")
        self.callees_context = QtWidgets.QCheckBox("Direct callees (5)")
        self.strings_context = QtWidgets.QCheckBox("Referenced strings (20)")
        self.imports_context = QtWidgets.QCheckBox("Referenced imports (20)")
        self.types_context = QtWidgets.QCheckBox("Relevant types")
        context_checks = (
            self.selection_context,
            self.callers_context,
            self.callees_context,
            self.strings_context,
            self.imports_context,
            self.types_context,
        )
        for check in context_checks:
            options_layout.addWidget(check)
            check.toggled.connect(
                lambda *_args: self.contextOptionsChanged.emit()
            )
        context_page_layout.addWidget(options_group)

        preview_row = QtWidgets.QHBoxLayout()
        preview_label = QtWidgets.QLabel("Exact request preview")
        preview_font = preview_label.font()
        preview_font.setWeight(QtGui.QFont.Weight.DemiBold)
        preview_label.setFont(preview_font)
        self.preview_button = QtWidgets.QPushButton("Build preview")
        preview_row.addWidget(preview_label)
        preview_row.addStretch(1)
        preview_row.addWidget(self.preview_button)
        context_page_layout.addLayout(preview_row)
        self.context_preview = QtWidgets.QPlainTextEdit()
        self.context_preview.setReadOnly(True)
        self.context_preview.setPlaceholderText(
            "Build a preview to inspect the exact context snapshot."
        )
        self.context_preview.setAccessibleName("Exact provider context preview")
        self.context_preview.setMinimumHeight(120)
        context_page_layout.addWidget(self.context_preview, 1)

        self.settings_page = SettingsPage()
        self.pages.addWidget(chat_page)
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(context_page)

        self.chat_tab_button.clicked.connect(self.show_chat)
        self.settings_tab_button.clicked.connect(self.show_settings)
        self.context_button.clicked.connect(self.show_context)
        self.context_back_button.clicked.connect(self.show_chat)
        self.clear_button.clicked.connect(lambda *_: self.clearRequested.emit())
        self.export_button.clicked.connect(lambda *_: self.exportRequested.emit())
        self.explain_button.clicked.connect(lambda *_: self.explainRequested.emit())
        self.ask_button.clicked.connect(lambda *_: self.askRequested.emit())
        self.prompt.submitRequested.connect(self.askRequested.emit)
        self.stop_button.clicked.connect(lambda *_: self.stopRequested.emit())
        self.preview_button.clicked.connect(lambda *_: self.previewRequested.emit())
        self.compare_toggle.toggled.connect(self.comparison_panel.setVisible)
        self.setTabOrder(self.chat_tab_button, self.settings_tab_button)
        self.setTabOrder(self.settings_tab_button, self.context_button)
        self.setTabOrder(self.context_button, self.export_button)
        self.setTabOrder(self.export_button, self.clear_button)
        self.setTabOrder(self.clear_button, self.prompt)
        self.setTabOrder(self.prompt, self.ask_button)
        self.setTabOrder(self.ask_button, self.explain_button)
        self.setTabOrder(self.explain_button, self.compare_toggle)
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)

    def show_chat(self, *_args: object) -> None:
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)
        self.prompt.setFocus()

    def show_settings(self, *_args: object) -> None:
        self.settings_tab_button.setChecked(True)
        self.pages.setCurrentIndex(1)

    def show_context(self, *_args: object) -> None:
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(2)
        self.context_back_button.setFocus()

    def selected_context_options(self) -> ContextOptions:
        return ContextOptions(
            include_selection=self.selection_context.isChecked(),
            include_callers=self.callers_context.isChecked(),
            include_callees=self.callees_context.isChecked(),
            include_strings=self.strings_context.isChecked(),
            include_imports=self.imports_context.isChecked(),
            include_types=self.types_context.isChecked(),
        )

    def selected_comparison_backend(self) -> str:
        return str(self.compare_combo.currentData() or "")

    def set_context_snapshot(self, summary: str, preview: str) -> None:
        display_summary = summary if preview else "Not previewed"
        self.context_summary.setText(display_summary)
        self.context_summary.setToolTip(display_summary)
        self.context_preview.setPlainText(preview)

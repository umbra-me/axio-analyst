"""Widget construction for the Axio Analyst sidebar."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.version import VERSION
from .settings_page import SettingsPage


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
    stopRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._build_interface()

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
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
        self.version_label = QtWidgets.QLabel(f"v{VERSION}")
        self.version_label.setAccessibleName(f"Axio Analyst version {VERSION}")
        version_font = self.version_label.font()
        version_font.setPointSizeF(max(8.0, version_font.pointSizeF() - 1.0))
        self.version_label.setFont(version_font)
        header.addWidget(self.version_label)
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
        code_background = palette.color(
            QtGui.QPalette.ColorRole.AlternateBase
        ).name()
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
        chat_layout.addWidget(self.prompt)

        actions = QtWidgets.QHBoxLayout()
        self.explain_button = QtWidgets.QPushButton("Explain")
        self.explain_button.setToolTip("Explain the current function")
        self.ask_button = QtWidgets.QPushButton("Ask")
        self.ask_button.setToolTip("Send question (Ctrl+Enter)")
        self.ask_button.setDefault(True)
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.stop_button.setToolTip("Cancel the active request")
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
        disclosure_font.setPointSizeF(
            max(8.0, disclosure_font.pointSizeF() - 1.0)
        )
        self.disclosure.setFont(disclosure_font)
        chat_layout.addWidget(self.disclosure)

        self.settings_page = SettingsPage()
        self.pages.addWidget(chat_page)
        self.pages.addWidget(self.settings_page)

        self.chat_tab_button.clicked.connect(self.show_chat)
        self.settings_tab_button.clicked.connect(self.show_settings)
        self.clear_button.clicked.connect(lambda *_: self.clearRequested.emit())
        self.explain_button.clicked.connect(lambda *_: self.explainRequested.emit())
        self.ask_button.clicked.connect(lambda *_: self.askRequested.emit())
        self.prompt.submitRequested.connect(self.askRequested.emit)
        self.stop_button.clicked.connect(lambda *_: self.stopRequested.emit())
        self.setTabOrder(self.chat_tab_button, self.settings_tab_button)
        self.setTabOrder(self.settings_tab_button, self.prompt)
        self.setTabOrder(self.prompt, self.ask_button)
        self.setTabOrder(self.ask_button, self.explain_button)
        self.setTabOrder(self.explain_button, self.stop_button)
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)

    def show_chat(self, *_args: object) -> None:
        self.chat_tab_button.setChecked(True)
        self.pages.setCurrentIndex(0)
        self.prompt.setFocus()

    def show_settings(self, *_args: object) -> None:
        self.settings_tab_button.setChecked(True)
        self.pages.setCurrentIndex(1)

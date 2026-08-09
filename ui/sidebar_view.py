"""Widget construction for the Axio Analyst sidebar.

The resting chat surface is deliberately two bands: one header row and one
composer. Everything else is conditional. Secondary actions live in the header
overflow menu, request scope lives on a chip inside the composer, and the
status line reveals itself only while it has something to say. An empty
conversation shows suggested questions rather than a greeting message, which is
where Explain becomes discoverable without competing with Ask for space.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import ContextOptions
from ..core.version import VERSION
from . import branding
from .settings_page import SettingsPage

TIGHT_SPACING = 4
ROW_SPACING = 8
SECTION_SPACING = 12

#: Below this dock width the composer drops its keyboard hint.
NARROW_WIDTH = 300

#: How long a finished status message stays on screen before it hides again.
STATUS_LINGER_MS = 6000

CHAT_PAGE = 0
SETTINGS_PAGE = 1
CONTEXT_PAGE = 2

CHROME_TONE = "chrome"
ACTION_TONE = "action"

COMPARISON_CHOICES = (
    ("No comparison", ""),
    ("Claude Code", "claude-code"),
    ("Codex", "codex-cli"),
    ("Ollama Cloud", "ollama-cloud"),
)

SUGGESTED_QUESTIONS = (
    "Explain what this function does",
    "Trace how each argument is used",
    "What can a caller control here?",
    "Find unchecked assumptions",
)


def shrink(widget: QtWidgets.QWidget, delta: float = -1.0) -> QtWidgets.QWidget:
    font = widget.font()
    font.setPointSizeF(max(8.0, font.pointSizeF() + delta))
    widget.setFont(font)
    return widget


def emphasize(widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
    font = widget.font()
    font.setWeight(QtGui.QFont.Weight.DemiBold)
    widget.setFont(font)
    return widget


def separator() -> QtWidgets.QFrame:
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
    line.setFixedHeight(1)
    return line


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

    def full_text(self) -> str:
        return self._full_text

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


class StatusLine(QtWidgets.QWidget):
    """A status row that stays hidden until it has something to report.

    Every existing caller writes through ``setText`` on the message label, so
    revealing the row is driven from the label itself rather than from a
    parallel API that a caller could forget to use.
    """

    class _Message(ElidingLabel):
        def __init__(self, owner: "StatusLine"):
            self._owner = owner
            super().__init__()

        def setText(self, text: str) -> None:
            super().setText(text)
            owner = getattr(self, "_owner", None)
            if owner is not None:
                owner.report(text)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        # The message label reports back from its own constructor, so ignore
        # anything it says until this row is fully built.
        self._live = False
        self._held = False
        self._hide_timer = QtCore.QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_if_released)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ROW_SPACING)
        self.message = self._Message(self)
        self.message.setAccessibleName("Request status")
        self.elapsed = QtWidgets.QLabel()
        self.elapsed.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.elapsed.setAccessibleName("Request elapsed time")
        layout.addWidget(self.message, 1)
        layout.addWidget(self.elapsed)
        self.hide()
        self._live = True

    def report(self, text: str) -> None:
        if not self._live:
            return
        if not text:
            self._hide_if_released()
            return
        self.show()
        if not self._held:
            self._hide_timer.start(STATUS_LINGER_MS)

    def hold(self) -> None:
        """Keep the row visible for the duration of a request."""
        self._held = True
        self._hide_timer.stop()
        if self.message.full_text():
            self.show()

    def release(self) -> None:
        self._held = False
        self._hide_timer.start(STATUS_LINGER_MS)

    def _hide_if_released(self) -> None:
        if not self._held:
            self.elapsed.clear()
            self.hide()


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


class SuggestionPanel(QtWidgets.QWidget):
    """Empty-conversation state: what this function is, and what to ask."""

    chosen = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(TIGHT_SPACING)
        layout.addStretch(2)

        self.title = ElidingLabel("No function selected")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        shrink(emphasize(self.title), 3.0)
        layout.addWidget(self.title)

        self.detail = QtWidgets.QLabel("Move the cursor into a function to begin.")
        self.detail.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.detail.setWordWrap(True)
        shrink(self.detail)
        layout.addWidget(self.detail)
        layout.addSpacing(14)

        self.lead = QtWidgets.QLabel("Ask about this function, or start with:")
        self.lead.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)
        self.lead.setWordWrap(True)
        shrink(self.lead)
        layout.addWidget(self.lead)
        layout.addSpacing(TIGHT_SPACING)

        self.buttons: list[QtWidgets.QPushButton] = []
        for question in SUGGESTED_QUESTIONS:
            button = QtWidgets.QPushButton(question)
            button.setStyleSheet("text-align: left; padding: 7px 10px;")
            shrink(button)
            button.clicked.connect(
                lambda *_args, text=question: self.chosen.emit(text)
            )
            self.buttons.append(button)
            layout.addWidget(button)
        layout.addStretch(3)

    def set_scope(self, title: str, detail: str, ready: bool) -> None:
        self.title.setText(title)
        self.detail.setText(detail)
        self.lead.setVisible(ready)
        for button in self.buttons:
            button.setVisible(ready)
            button.setEnabled(ready)


class SidebarView(QtWidgets.QWidget):
    askRequested = QtCore.Signal()
    clearRequested = QtCore.Signal()
    explainRequested = QtCore.Signal()
    exportRequested = QtCore.Signal()
    contextOptionsChanged = QtCore.Signal()
    previewRequested = QtCore.Signal()
    stopRequested = QtCore.Signal()
    suggestionChosen = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._glyph_buttons: list[tuple[QtWidgets.QAbstractButton, str, str]] = []
        self._dim_widgets: list[QtWidgets.QWidget] = []
        self._scope_name = ""
        self._narrow = False
        self._ready = False
        self._build_interface()
        self._apply_theme()
        self._ready = True

    # -- construction -----------------------------------------------------

    def _glyph_button(
        self,
        name: str,
        text: str = "",
        *,
        tone: str = CHROME_TONE,
        size: int = 18,
    ) -> QtWidgets.QToolButton:
        button = QtWidgets.QToolButton()
        button.setAutoRaise(True)
        button.setIconSize(QtCore.QSize(size, size))
        button.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        if text:
            button.setText(text)
            button.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            )
        self._glyph_buttons.append((button, name, tone))
        return button

    def _dim(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        self._dim_widgets.append(widget)
        return widget

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 8)
        root.setSpacing(ROW_SPACING)

        self.pages = QtWidgets.QStackedWidget()
        root.addWidget(self.pages, 1)

        self.pages.addWidget(self._build_chat_page())
        self.settings_page = SettingsPage()
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self._build_context_page())

        self._connect()
        self.pages.setCurrentIndex(CHAT_PAGE)

    def _build_header(self, layout: QtWidgets.QVBoxLayout) -> None:
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(TIGHT_SPACING)
        self.context_name = emphasize(ElidingLabel("No function selected"))
        self.context_detail = self._dim(shrink(ElidingLabel()))
        self.context_detail.setAccessibleName("Current function address")
        self.context_detail.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )

        self.settings_button = self._glyph_button("settings")
        self.settings_button.setCheckable(True)
        self.settings_button.setToolTip("Axio Analyst settings")
        self.settings_button.setAccessibleName("Show Axio Analyst settings")

        self.overflow_button = self._glyph_button("overflow")
        self.overflow_button.setToolTip("More actions")
        self.overflow_button.setAccessibleName("More actions")
        menu = QtWidgets.QMenu(self.overflow_button)
        self.version_action = menu.addAction(f"Axio Analyst v{VERSION}")
        self.version_action.setEnabled(False)
        menu.addSeparator()
        self.explain_action = menu.addAction("Explain this function")
        self.compare_menu = menu.addMenu("Compare with")
        self.comparison_group = QtGui.QActionGroup(self)
        self.comparison_group.setExclusive(True)
        for label, backend in COMPARISON_CHOICES:
            action = self.compare_menu.addAction(label)
            action.setCheckable(True)
            action.setData(backend)
            action.setChecked(not backend)
            self.comparison_group.addAction(action)
        menu.addSeparator()
        self.export_action = menu.addAction("Export conversation...")
        self.clear_action = menu.addAction("Clear conversation")
        self.overflow_menu = menu
        self.overflow_button.setMenu(menu)
        self.overflow_button.setPopupMode(
            QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup
        )
        # The glyph already reads as a menu; the extra arrow only crowds it.
        self.overflow_button.setStyleSheet(
            "QToolButton::menu-indicator { image: none; }"
        )

        # Both labels elide, so they need explicit stretch to share the row.
        header.addWidget(self.context_name, 3)
        header.addWidget(self.context_detail, 2)
        header.addWidget(self.settings_button)
        header.addWidget(self.overflow_button)
        layout.addLayout(header)
        layout.addWidget(separator())

    def _build_composer(self, layout: QtWidgets.QVBoxLayout) -> None:
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setAccessibleName("Request progress")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        composer = QtWidgets.QFrame()
        composer.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        composer_layout = QtWidgets.QVBoxLayout(composer)
        composer_layout.setContentsMargins(6, 4, 4, 4)
        composer_layout.setSpacing(TIGHT_SPACING)

        self.prompt = PromptEdit()
        self.prompt.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.prompt.setPlaceholderText("Ask about this function...")
        self.prompt.setAccessibleName("Question about current function")
        self.prompt.setFixedHeight(
            max(42, self.prompt.fontMetrics().lineSpacing() * 2 + 10)
        )
        self.prompt.setTabChangesFocus(True)
        composer_layout.addWidget(self.prompt)

        controls = QtWidgets.QHBoxLayout()
        controls.setSpacing(TIGHT_SPACING)
        self.context_button = self._glyph_button("scope", "context", size=15)
        self.context_button.setAccessibleName("Request context")
        self._dim(shrink(self.context_button))
        self.shortcut_hint = self._dim(shrink(QtWidgets.QLabel("Ctrl+Enter")))

        self.ask_button = self._glyph_button("send", tone=ACTION_TONE, size=17)
        self.ask_button.setToolTip("Send question (Ctrl+Enter)")
        self.ask_button.setAccessibleName("Send question")
        self.stop_button = self._glyph_button("stop", tone=ACTION_TONE, size=17)
        self.stop_button.setToolTip("Cancel the active request")
        self.stop_button.setAccessibleName("Stop request")
        self.submit_action = QtWidgets.QStackedWidget()
        self.submit_action.addWidget(self.ask_button)
        self.submit_action.addWidget(self.stop_button)
        self.submit_action.setFixedSize(self.ask_button.sizeHint())

        controls.addWidget(self.context_button)
        controls.addStretch(1)
        controls.addWidget(self.shortcut_hint)
        controls.addWidget(self.submit_action)
        composer_layout.addLayout(controls)
        layout.addWidget(composer)

        self.status_line = StatusLine()
        self._dim(self.status_line.message)
        self._dim(shrink(self.status_line.elapsed))
        layout.addWidget(self.status_line)

    def _build_chat_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TIGHT_SPACING)

        self._build_header(layout)

        self.conversation_area = QtWidgets.QStackedWidget()
        self.suggestions = SuggestionPanel()
        self.transcript = QtWidgets.QTextBrowser()
        self.transcript.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setUndoRedoEnabled(False)
        self.transcript.setAccessibleName("Axio Analyst conversation")
        self.transcript.setMinimumHeight(120)
        self.transcript.document().setDocumentMargin(2)
        self.conversation_area.addWidget(self.suggestions)
        self.conversation_area.addWidget(self.transcript)
        layout.addWidget(self.conversation_area, 1)

        self._build_composer(layout)
        return page

    def _build_context_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(ROW_SPACING)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(TIGHT_SPACING)
        self.context_back_button = self._glyph_button("back")
        self.context_back_button.setToolTip("Back to the conversation")
        self.context_back_button.setAccessibleName("Back to conversation")
        header.addWidget(self.context_back_button)
        header.addWidget(emphasize(QtWidgets.QLabel("Request context")), 1)
        layout.addLayout(header)

        note = self._dim(
            shrink(
                QtWidgets.QLabel(
                    "The current function is always included. Add only the "
                    "nearby evidence this request needs."
                )
            )
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addWidget(separator())

        self.selection_context = QtWidgets.QCheckBox("Current selection")
        self.callers_context = QtWidgets.QCheckBox("Direct callers (3)")
        self.callees_context = QtWidgets.QCheckBox("Direct callees (5)")
        self.strings_context = QtWidgets.QCheckBox("Referenced strings (20)")
        self.imports_context = QtWidgets.QCheckBox("Referenced imports (20)")
        self.types_context = QtWidgets.QCheckBox("Relevant types")
        for check in self.context_checks():
            layout.addWidget(check)
            check.toggled.connect(lambda *_args: self.contextOptionsChanged.emit())

        layout.addWidget(separator())
        preview_row = QtWidgets.QHBoxLayout()
        preview_row.setSpacing(TIGHT_SPACING)
        self.context_summary = self._dim(
            shrink(ElidingLabel("Current function only · not previewed"))
        )
        self.context_summary.setAccessibleName("Context snapshot summary")
        self.preview_button = QtWidgets.QPushButton("Build preview")
        self.preview_button.setAccessibleName("Build exact context preview")
        preview_row.addWidget(self.context_summary, 1)
        preview_row.addWidget(self.preview_button)
        layout.addLayout(preview_row)

        self.context_preview = QtWidgets.QPlainTextEdit()
        self.context_preview.setReadOnly(True)
        self.context_preview.setPlaceholderText(
            "Build a preview to inspect the exact context snapshot."
        )
        self.context_preview.setAccessibleName("Exact provider context preview")
        self.context_preview.setMinimumHeight(120)
        layout.addWidget(self.context_preview, 1)
        return page

    def _connect(self) -> None:
        self.settings_button.toggled.connect(self._settings_toggled)
        self.context_button.clicked.connect(self.show_context)
        self.context_back_button.clicked.connect(self.show_chat)
        self.settings_page.backRequested.connect(self.show_chat)
        self.clear_action.triggered.connect(lambda *_: self.clearRequested.emit())
        self.export_action.triggered.connect(lambda *_: self.exportRequested.emit())
        self.explain_action.triggered.connect(
            lambda *_: self.explainRequested.emit()
        )
        self.ask_button.clicked.connect(lambda *_: self.askRequested.emit())
        self.prompt.submitRequested.connect(self.askRequested.emit)
        self.stop_button.clicked.connect(lambda *_: self.stopRequested.emit())
        self.preview_button.clicked.connect(lambda *_: self.previewRequested.emit())
        self.suggestions.chosen.connect(self.suggestionChosen.emit)

        self.setTabOrder(self.settings_button, self.overflow_button)
        self.setTabOrder(self.overflow_button, self.transcript)
        self.setTabOrder(self.transcript, self.prompt)
        self.setTabOrder(self.prompt, self.context_button)
        self.setTabOrder(self.context_button, self.ask_button)
        self.setTabOrder(self.ask_button, self.stop_button)
        self.setTabOrder(self.context_back_button, self.selection_context)
        self.setTabOrder(self.types_context, self.preview_button)

    # -- theming and responsiveness ---------------------------------------

    def _apply_theme(self) -> None:
        palette = self.palette()
        muted = palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        tones = {
            CHROME_TONE: muted,
            ACTION_TONE: palette.color(QtGui.QPalette.ColorRole.WindowText),
        }
        for button, name, tone in self._glyph_buttons:
            button.setIcon(branding.glyph_icon(name, tones[tone]))
        self.compare_menu.setIcon(branding.glyph_icon("compare", muted))
        for widget in self._dim_widgets:
            widget_palette = widget.palette()
            widget_palette.setColor(QtGui.QPalette.ColorRole.WindowText, muted)
            widget_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, muted)
            widget.setPalette(widget_palette)

        window = palette.color(QtGui.QPalette.ColorRole.Window)
        for editor in (self.transcript, self.prompt):
            editor_palette = editor.palette()
            editor_palette.setColor(QtGui.QPalette.ColorRole.Base, window)
            editor.setPalette(editor_palette)
        for label in (self.suggestions.detail, self.suggestions.lead):
            label_palette = label.palette()
            label_palette.setColor(QtGui.QPalette.ColorRole.WindowText, muted)
            label.setPalette(label_palette)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self._apply_theme()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        narrow = self.width() < NARROW_WIDTH
        if not self._ready:
            return
        self.refresh_scope_disclosure()
        if narrow == self._narrow:
            return
        self._narrow = narrow
        self.shortcut_hint.setVisible(not narrow)
        self.settings_page.set_narrow(narrow)

    # -- navigation --------------------------------------------------------

    def _settings_toggled(self, checked: bool) -> None:
        if checked:
            self.pages.setCurrentIndex(SETTINGS_PAGE)
        elif self.pages.currentIndex() == SETTINGS_PAGE:
            self.pages.setCurrentIndex(CHAT_PAGE)
            self.prompt.setFocus()

    def show_chat(self, *_args: object) -> None:
        self.settings_button.setChecked(False)
        self.pages.setCurrentIndex(CHAT_PAGE)
        self.prompt.setFocus()

    def show_settings(self, *_args: object) -> None:
        self.settings_button.setChecked(True)

    def show_context(self, *_args: object) -> None:
        self.settings_button.setChecked(False)
        self.pages.setCurrentIndex(CONTEXT_PAGE)
        self.context_back_button.setFocus()

    # -- state -------------------------------------------------------------

    def context_checks(self) -> tuple[QtWidgets.QCheckBox, ...]:
        return (
            self.selection_context,
            self.callers_context,
            self.callees_context,
            self.strings_context,
            self.imports_context,
            self.types_context,
        )

    def selected_context_options(self) -> ContextOptions:
        return ContextOptions(
            include_selection=self.selection_context.isChecked(),
            include_callers=self.callers_context.isChecked(),
            include_callees=self.callees_context.isChecked(),
            include_strings=self.strings_context.isChecked(),
            include_imports=self.imports_context.isChecked(),
            include_types=self.types_context.isChecked(),
        )

    def enabled_pack_count(self) -> int:
        return sum(1 for check in self.context_checks() if check.isChecked())

    def selected_comparison_backend(self) -> str:
        action = self.comparison_group.checkedAction()
        return str(action.data() or "") if action is not None else ""

    def clear_comparison(self) -> None:
        for action in self.comparison_group.actions():
            if not action.data():
                action.setChecked(True)
                return

    def set_comparison_enabled(self, enabled: bool) -> None:
        self.compare_menu.setEnabled(enabled)

    def set_scope(self, name: str, address: str, detail: str, ready: bool) -> None:
        self._scope_name = name if ready else ""
        self.context_name.setText(name)
        self.context_detail.setText(address)
        self.context_detail.set_detail_tooltip(detail)
        self.suggestions.set_scope(name, detail, ready)
        self.prompt.setPlaceholderText(
            f"Ask about {name}..." if ready else "Ask about this function..."
        )
        self.refresh_scope_disclosure()

    def set_conversation_empty(self, empty: bool) -> None:
        self.conversation_area.setCurrentWidget(
            self.suggestions if empty else self.transcript
        )

    def refresh_scope_disclosure(self) -> None:
        """Keep the opt-in extra-context state visible at every dock width.

        The chip is the disclosure: it names the scope and always shows the
        pack count, eliding the function name rather than the ``+N`` when the
        dock is too narrow for both.
        """
        packs = self.enabled_pack_count()
        suffix = f" +{packs}" if packs else ""
        name = self._scope_name or "context"
        budget = max(48, int(self.width() * 0.42))
        metrics = self.context_button.fontMetrics()
        available = budget - metrics.horizontalAdvance(suffix) - 26
        elided = metrics.elidedText(
            name, QtCore.Qt.TextElideMode.ElideRight, max(24, available)
        )
        self.context_button.setText(f"{elided}{suffix}")
        if packs:
            enabled = ", ".join(
                check.text() for check in self.context_checks() if check.isChecked()
            )
            self.context_button.setToolTip(
                "Request context: current function plus "
                f"{packs} opt-in pack{'s' if packs != 1 else ''} ({enabled}). "
                "Choose to review or preview the exact snapshot."
            )
        else:
            self.context_button.setToolTip(
                "Request context: current function only. Choose to add "
                "bounded opt-in packs or preview the exact snapshot."
            )

    def set_context_snapshot(self, summary: str, preview: str) -> None:
        display_summary = summary if preview else "Not previewed"
        self.context_summary.setText(display_summary)
        self.context_preview.setPlainText(preview)

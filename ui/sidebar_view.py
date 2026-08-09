"""Widget construction for the Axio Analyst sidebar.

The chat surface is deliberately flat: the prompt editor is the only framed
element, so the transcript reads as the primary surface instead of one panel
among several. Secondary actions live in an overflow menu and the comparison
provider lives under the Ask button, which keeps the resting layout to one
action row and one status strip.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.models import ContextOptions
from ..core.version import VERSION
from . import branding
from .settings_page import SettingsPage

TIGHT_SPACING = 4
ROW_SPACING = 8
SECTION_SPACING = 12

#: Below this dock width the action row drops button text and keeps glyphs.
NARROW_WIDTH = 300

CHROME_TONE = "chrome"
ACTION_TONE = "action"
PRIMARY_TONE = "primary"

CHAT_PAGE = 0
SETTINGS_PAGE = 1
CONTEXT_PAGE = 2

COMPARISON_CHOICES = (
    ("No comparison", ""),
    ("Claude Code", "claude-code"),
    ("Codex", "codex-cli"),
    ("Ollama Cloud", "ollama-cloud"),
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


def separator() -> QtWidgets.QFrame:
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
    line.setFixedHeight(1)
    return line


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
        self._glyph_buttons: list[tuple[QtWidgets.QAbstractButton, str, str]] = []
        self._dim_widgets: list[QtWidgets.QWidget] = []
        self._collapsible_labels: list[QtWidgets.QToolButton] = []
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
    ) -> QtWidgets.QToolButton:
        button = QtWidgets.QToolButton()
        button.setAutoRaise(tone != PRIMARY_TONE)
        button.setIconSize(QtCore.QSize(18, 18))
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
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(ROW_SPACING)

        self.pages = QtWidgets.QStackedWidget()
        root.addWidget(self.pages, 1)

        self.pages.addWidget(self._build_chat_page())
        self.settings_page = SettingsPage()
        self.pages.addWidget(self.settings_page)
        self.pages.addWidget(self._build_context_page())

        self._connect()
        self.pages.setCurrentIndex(CHAT_PAGE)

    def _build_chat_page(self) -> QtWidgets.QWidget:
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TIGHT_SPACING)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(TIGHT_SPACING)
        self.context_name = emphasize(ElidingLabel("No function selected"))
        self.settings_button = self._glyph_button("settings")
        self.settings_button.setCheckable(True)
        self.settings_button.setToolTip("Axio Analyst settings")
        self.settings_button.setAccessibleName("Show Axio Analyst settings")
        self.overflow_button = self._glyph_button("overflow")
        self.overflow_button.setToolTip("Conversation actions")
        self.overflow_button.setAccessibleName("Conversation actions")
        self.overflow_menu = QtWidgets.QMenu(self.overflow_button)
        self.export_action = self.overflow_menu.addAction("Export conversation...")
        self.clear_action = self.overflow_menu.addAction("Clear conversation")
        self.overflow_button.setMenu(self.overflow_menu)
        self.overflow_button.setPopupMode(
            QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup
        )
        header.addWidget(self.context_name, 1)
        header.addWidget(self.settings_button)
        header.addWidget(self.overflow_button)
        layout.addLayout(header)

        header_detail = QtWidgets.QHBoxLayout()
        header_detail.setSpacing(ROW_SPACING)
        self.context_detail = self._dim(
            shrink(ElidingLabel("Move the cursor into a function to begin."))
        )
        self.version_label = QtWidgets.QLabel(f"v{VERSION}")
        self.version_label.setAccessibleName(f"Axio Analyst version {VERSION}")
        self.version_label.setToolTip(f"Axio Analyst version {VERSION}")
        self._dim(shrink(self.version_label))
        header_detail.addWidget(self.context_detail, 1)
        header_detail.addWidget(self.version_label)
        layout.addLayout(header_detail)
        layout.addSpacing(TIGHT_SPACING)
        layout.addWidget(separator())

        self.transcript = QtWidgets.QTextBrowser()
        self.transcript.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.transcript.setOpenLinks(False)
        self.transcript.setOpenExternalLinks(False)
        self.transcript.setUndoRedoEnabled(False)
        self.transcript.setAccessibleName("Axio Analyst conversation")
        self.transcript.setMinimumHeight(160)
        self.transcript.document().setDocumentMargin(2)
        layout.addWidget(self.transcript, 1)

        self.prompt = PromptEdit()
        self.prompt.setPlaceholderText(
            "Ask about this function...    Ctrl+Enter to send"
        )
        self.prompt.setAccessibleName("Question about current function")
        self.prompt.setFixedHeight(
            max(54, self.prompt.fontMetrics().lineSpacing() * 3 + 14)
        )
        self.prompt.setTabChangesFocus(True)
        layout.addWidget(self.prompt)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(TIGHT_SPACING)
        self.context_button = self._glyph_button(
            "scope", "Context", tone=ACTION_TONE
        )
        self.context_button.setAccessibleName("Request context")
        self.explain_button = self._glyph_button(
            "explain", "Explain", tone=ACTION_TONE
        )
        self.explain_button.setToolTip("Explain the current function")
        self.explain_button.setAccessibleName("Explain current function")

        self.ask_button = self._glyph_button("send", "Ask", tone=PRIMARY_TONE)
        self.ask_button.setToolTip("Send question (Ctrl+Enter)")
        self.ask_button.setAccessibleName("Send question")
        self.ask_menu = QtWidgets.QMenu(self.ask_button)
        self.comparison_group = QtGui.QActionGroup(self)
        self.comparison_group.setExclusive(True)
        compare_menu = self.ask_menu.addMenu("Compare with")
        compare_menu.setIcon(self._compare_icon())
        for label, backend in COMPARISON_CHOICES:
            action = compare_menu.addAction(label)
            action.setCheckable(True)
            action.setData(backend)
            action.setChecked(not backend)
            self.comparison_group.addAction(action)
        self.compare_menu = compare_menu
        self.ask_button.setMenu(self.ask_menu)
        self.ask_button.setPopupMode(
            QtWidgets.QToolButton.ToolButtonPopupMode.MenuButtonPopup
        )

        self.stop_button = self._glyph_button("stop", "Stop", tone=PRIMARY_TONE)
        self.stop_button.setToolTip("Cancel the active request")
        self.stop_button.setAccessibleName("Stop request")

        self.submit_action = QtWidgets.QStackedWidget()
        self.submit_action.addWidget(self.ask_button)
        self.submit_action.addWidget(self.stop_button)
        self.submit_action.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.submit_action.setMinimumWidth(96)
        self.submit_action.setFixedHeight(self.ask_button.sizeHint().height())

        actions.addWidget(self.context_button)
        actions.addStretch(1)
        actions.addWidget(self.explain_button)
        actions.addWidget(self.submit_action)
        layout.addLayout(actions)

        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(ROW_SPACING)
        self.status_label = self._dim(shrink(ElidingLabel("Ready")))
        self.status_label.setAccessibleName("Request status")
        self.backend_label = self._dim(shrink(ElidingLabel()))
        self.backend_label.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.backend_label.setAccessibleName("Configured provider")
        self.elapsed_label = self._dim(shrink(QtWidgets.QLabel()))
        self.elapsed_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.elapsed_label.setAccessibleName("Request elapsed time")
        status_row.addWidget(self.status_label, 3)
        status_row.addWidget(self.backend_label, 4)
        status_row.addWidget(self.elapsed_label)
        layout.addLayout(status_row)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setAccessibleName("Request progress")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
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
        self.preview_button = self._glyph_button(
            "preview", "Build preview", tone=PRIMARY_TONE
        )
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
        self.explain_button.clicked.connect(lambda *_: self.explainRequested.emit())
        self.ask_button.clicked.connect(lambda *_: self.askRequested.emit())
        self.prompt.submitRequested.connect(self.askRequested.emit)
        self.stop_button.clicked.connect(lambda *_: self.stopRequested.emit())
        self.preview_button.clicked.connect(lambda *_: self.previewRequested.emit())

        self.setTabOrder(self.settings_button, self.overflow_button)
        self.setTabOrder(self.overflow_button, self.transcript)
        self.setTabOrder(self.transcript, self.prompt)
        self.setTabOrder(self.prompt, self.context_button)
        self.setTabOrder(self.context_button, self.explain_button)
        self.setTabOrder(self.explain_button, self.ask_button)
        self.setTabOrder(self.ask_button, self.stop_button)
        self.setTabOrder(self.context_back_button, self.selection_context)
        self.setTabOrder(self.types_context, self.preview_button)

    # -- theming and responsiveness ---------------------------------------

    def _compare_icon(self) -> QtGui.QIcon:
        return branding.glyph_icon(
            "compare",
            self.palette().color(QtGui.QPalette.ColorRole.WindowText),
        )

    def _apply_theme(self) -> None:
        palette = self.palette()
        foreground = palette.color(QtGui.QPalette.ColorRole.WindowText)
        muted = palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        tones = {
            CHROME_TONE: muted,
            ACTION_TONE: foreground,
            PRIMARY_TONE: palette.color(QtGui.QPalette.ColorRole.ButtonText),
        }
        for button, name, tone in self._glyph_buttons:
            button.setIcon(branding.glyph_icon(name, tones[tone]))
        for widget in self._dim_widgets:
            widget_palette = widget.palette()
            widget_palette.setColor(QtGui.QPalette.ColorRole.WindowText, muted)
            widget.setPalette(widget_palette)
        self.compare_menu.setIcon(branding.glyph_icon("compare", foreground))

        transcript_palette = self.transcript.palette()
        transcript_palette.setColor(
            QtGui.QPalette.ColorRole.Base,
            palette.color(QtGui.QPalette.ColorRole.Window),
        )
        self.transcript.setPalette(transcript_palette)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self._apply_theme()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        narrow = self.width() < NARROW_WIDTH
        if not self._ready or narrow == self._narrow:
            return
        self._narrow = narrow
        self.explain_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
            if narrow
            else QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.settings_page.set_narrow(narrow)
        self.refresh_scope_disclosure()

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

    def refresh_scope_disclosure(self) -> None:
        """Keep the opt-in extra-context state visible at every dock width.

        A narrow dock drops the word ``Context`` but never the pack count, so
        the non-default state stays legible where space is scarcest.
        """
        packs = self.enabled_pack_count()
        if packs:
            enabled = ", ".join(
                check.text() for check in self.context_checks() if check.isChecked()
            )
            self.context_button.setText(
                f"+{packs}" if self._narrow else f"Context +{packs}"
            )
            self.context_button.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            )
            self.context_button.setToolTip(
                "Request context: current function plus "
                f"{packs} opt-in pack{'s' if packs != 1 else ''} ({enabled}). "
                "Choose to review or preview the exact snapshot."
            )
        else:
            self.context_button.setText("" if self._narrow else "Context")
            self.context_button.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonIconOnly
                if self._narrow
                else QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
            )
            self.context_button.setToolTip(
                "Request context: current function only. Choose to add "
                "bounded opt-in packs or preview the exact snapshot."
            )

    def set_context_snapshot(self, summary: str, preview: str) -> None:
        display_summary = summary if preview else "Not previewed"
        self.context_summary.setText(display_summary)
        self.context_preview.setPlainText(preview)

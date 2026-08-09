"""Native settings surface for Axio Analyst.

Only the provider choice is always expanded. Executables, request limits, and
local history collapse behind one-line summaries so a narrow Binary Ninja dock
shows a short list of decisions instead of four stacked forms.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from ..core.version import VERSION
from ..host.settings import (
    BACKEND_LABELS,
    MODEL_CHOICES,
    REASONING_EFFORTS,
    SidebarPreferences,
    get_provider_selection,
    get_runtime_config,
    get_sidebar_preferences,
    set_backend,
    set_provider_selection,
    set_sidebar_preferences,
)
from . import branding

TIGHT_SPACING = 4
ROW_SPACING = 8
SECTION_SPACING = 12


class CollapsibleSection(QtWidgets.QWidget):
    """A flat section header that reveals its form on demand."""

    def __init__(self, title: str, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TIGHT_SPACING)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(TIGHT_SPACING)
        self.toggle = QtWidgets.QToolButton()
        self.toggle.setText(title)
        self.toggle.setCheckable(True)
        self.toggle.setAutoRaise(True)
        self.toggle.setIconSize(QtCore.QSize(16, 16))
        self.toggle.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.toggle.setAccessibleName(f"{title} settings")
        self._summary_text = ""
        self.summary = QtWidgets.QLabel()
        self.summary.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight
            | QtCore.Qt.AlignmentFlag.AlignVCenter
        )
        self.summary.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.summary.installEventFilter(self)
        header.addWidget(self.toggle)
        header.addWidget(self.summary, 1)
        layout.addLayout(header)

        self.content = QtWidgets.QWidget()
        self.form = QtWidgets.QFormLayout(self.content)
        self.form.setContentsMargins(0, 0, 0, TIGHT_SPACING)
        self.form.setSpacing(TIGHT_SPACING)
        self.form.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.content.setVisible(False)
        layout.addWidget(self.content)
        self.toggle.toggled.connect(self.content.setVisible)
        self.toggle.toggled.connect(lambda *_: self._render_summary())

    def eventFilter(
        self,
        watched: QtCore.QObject,
        event: QtCore.QEvent,
    ) -> bool:
        if watched is self.summary and event.type() == QtCore.QEvent.Type.Resize:
            self._render_summary()
        return super().eventFilter(watched, event)

    def _render_summary(self) -> None:
        """An expanded section already shows its values, so drop the echo."""
        if self.toggle.isChecked():
            self.summary.setText("")
            return
        width = max(0, self.summary.contentsRect().width())
        self.summary.setText(
            self.summary.fontMetrics().elidedText(
                self._summary_text,
                QtCore.Qt.TextElideMode.ElideRight,
                width,
            )
        )

    def set_summary(self, text: str) -> None:
        self._summary_text = text
        self.summary.setToolTip(text)
        self._render_summary()

    def set_narrow(self, narrow: bool) -> None:
        self.form.setRowWrapPolicy(
            QtWidgets.QFormLayout.RowWrapPolicy.WrapAllRows
            if narrow
            else QtWidgets.QFormLayout.RowWrapPolicy.DontWrapRows
        )


class SettingsPage(QtWidgets.QWidget):
    applied = QtCore.Signal()
    backRequested = QtCore.Signal()
    providerChanged = QtCore.Signal(str)
    refreshModelsRequested = QtCore.Signal()
    selectionChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._active_backend = "claude-code"
        self._draft_selections: dict[str, tuple[str, str]] = {}
        self._sections: list[CollapsibleSection] = []
        self._dim_widgets: list[QtWidgets.QWidget] = []
        self._narrow = False
        self._build_interface()
        self._apply_theme()
        self.load()

    # -- construction -----------------------------------------------------

    def _dim(self, widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        font = widget.font()
        font.setPointSizeF(max(8.0, font.pointSizeF() - 1.0))
        widget.setFont(font)
        self._dim_widgets.append(widget)
        return widget

    @staticmethod
    def _wrap(label: QtWidgets.QLabel) -> QtWidgets.QLabel:
        """Word wrap without clipping inside the settings scroll area.

        A layout only reserves room for a wrapped label when its size policy
        advertises height-for-width, which QLabel does not do on its own.
        """
        label.setWordWrap(True)
        policy = label.sizePolicy()
        policy.setHeightForWidth(True)
        policy.setVerticalPolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        label.setSizePolicy(policy)
        return label

    @staticmethod
    def _separator() -> QtWidgets.QFrame:
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        return line

    def _section(self, title: str) -> CollapsibleSection:
        section = CollapsibleSection(title)
        self._sections.append(section)
        self._dim(section.summary)
        return section

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(ROW_SPACING)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(TIGHT_SPACING)
        self.back_button = QtWidgets.QToolButton()
        self.back_button.setAutoRaise(True)
        self.back_button.setIconSize(QtCore.QSize(18, 18))
        self.back_button.setToolTip("Back to the conversation")
        self.back_button.setAccessibleName("Back to conversation")
        title = QtWidgets.QLabel("Settings")
        title_font = title.font()
        title_font.setWeight(QtGui.QFont.Weight.DemiBold)
        title.setFont(title_font)
        header.addWidget(self.back_button)
        header.addWidget(title, 1)
        root.addLayout(header)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content = QtWidgets.QWidget()
        content.setMinimumWidth(0)
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(ROW_SPACING)

        intro = self._wrap(
            self._dim(
                QtWidgets.QLabel(
                    f"Axio Analyst v{VERSION}. Configure local harnesses and "
                    "request limits. Credentials remain inside each provider CLI."
                )
            )
        )
        content_layout.addWidget(intro)
        content_layout.addWidget(self._separator())

        self.provider_form = QtWidgets.QFormLayout()
        self.provider_form.setContentsMargins(0, 0, 0, 0)
        self.provider_form.setSpacing(TIGHT_SPACING)
        self.provider_form.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setAccessibleName("Analysis provider")
        for backend, label in BACKEND_LABELS.items():
            self.provider_combo.addItem(label, backend)

        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setInsertPolicy(QtWidgets.QComboBox.InsertPolicy.NoInsert)
        self.model_combo.setAccessibleName("Analysis model")
        self.model_combo.setToolTip("Choose a known model or type a full model name")
        self.model_combo.setMinimumWidth(0)

        model_row = QtWidgets.QWidget()
        model_layout = QtWidgets.QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        model_layout.setSpacing(TIGHT_SPACING)
        model_layout.addWidget(self.model_combo, 1)
        self.refresh_models_button = QtWidgets.QToolButton()
        self.refresh_models_button.setText("Refresh")
        self.refresh_models_button.setToolTip("Fetch available Ollama Cloud models")
        self.refresh_models_button.setAccessibleName("Refresh Ollama Cloud models")
        model_layout.addWidget(self.refresh_models_button)

        self.effort_combo = QtWidgets.QComboBox()
        self.effort_combo.setAccessibleName("Reasoning effort")

        self.provider_form.addRow("Provider", self.provider_combo)
        self.provider_form.addRow("Model", model_row)
        self.provider_form.addRow("Reasoning", self.effort_combo)
        content_layout.addLayout(self.provider_form)

        self.harness_section = self._section("Executables")
        self.claude_executable = self._executable_edit(
            "Claude Code executable", "claude"
        )
        self.codex_executable = self._executable_edit("Codex executable", "codex")
        self.ollama_executable = self._executable_edit("Ollama executable", "ollama")
        self.harness_section.form.addRow("Claude Code", self.claude_executable)
        self.harness_section.form.addRow("Codex", self.codex_executable)
        self.harness_section.form.addRow("Ollama", self.ollama_executable)
        content_layout.addWidget(self._separator())
        content_layout.addWidget(self.harness_section)

        self.limits_section = self._section("Request limits")
        self.timeout_seconds = QtWidgets.QSpinBox()
        self.timeout_seconds.setRange(10, 3600)
        self.timeout_seconds.setSingleStep(30)
        self.timeout_seconds.setSuffix(" s")
        self.timeout_seconds.setAccessibleName("Request timeout in seconds")
        self.max_context_chars = QtWidgets.QSpinBox()
        self.max_context_chars.setRange(1000, 500000)
        self.max_context_chars.setSingleStep(5000)
        self.max_context_chars.setSuffix(" chars")
        self.max_context_chars.setGroupSeparatorShown(True)
        self.max_context_chars.setAccessibleName("Maximum context characters")
        self.limits_section.form.addRow("Timeout", self.timeout_seconds)
        self.limits_section.form.addRow("Total context", self.max_context_chars)
        content_layout.addWidget(self._separator())
        content_layout.addWidget(self.limits_section)

        self.history_section = self._section("Local history")
        self.persist_conversations = QtWidgets.QCheckBox(
            "Restore conversations for this binary"
        )
        self.persist_conversations.setToolTip(
            "Store bounded transcripts under the Binary Ninja user directory"
        )
        self.persist_conversations.setAccessibleName(
            "Persist Axio Analyst conversations locally"
        )
        privacy_note = self._wrap(
            self._dim(
                QtWidgets.QLabel(
                    "Off by default. Storage uses a path-free content "
                    "fingerprint; Clear deletes the saved transcript and "
                    "Export writes Markdown."
                )
            )
        )
        self.history_section.form.addRow(self.persist_conversations)
        self.history_section.form.addRow(privacy_note)
        content_layout.addWidget(self._separator())
        content_layout.addWidget(self.history_section)

        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.status_label = self._wrap(self._dim(QtWidgets.QLabel()))
        self.status_label.setAccessibleName("Settings status")
        root.addWidget(self.status_label)

        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        self.revert_button = QtWidgets.QPushButton("Revert")
        self.revert_button.setToolTip("Reload saved settings")
        self.apply_button = QtWidgets.QPushButton("Apply")
        self.apply_button.setToolTip("Save these settings")
        self.apply_button.setDefault(True)
        actions.addWidget(self.revert_button)
        actions.addWidget(self.apply_button)
        root.addLayout(actions)

        self.back_button.clicked.connect(lambda *_: self.backRequested.emit())
        self.provider_combo.currentIndexChanged.connect(self._provider_changed)
        self.model_combo.activated.connect(self._selection_changed)
        if self.model_combo.lineEdit() is not None:
            self.model_combo.lineEdit().editingFinished.connect(
                self._selection_changed
            )
        self.effort_combo.currentIndexChanged.connect(self._selection_changed)
        self.refresh_models_button.clicked.connect(self._request_refresh)
        self.revert_button.clicked.connect(self.load)
        self.apply_button.clicked.connect(self.apply)
        for edit in (
            self.claude_executable,
            self.codex_executable,
            self.ollama_executable,
        ):
            edit.textChanged.connect(self._mark_dirty)
        self.timeout_seconds.valueChanged.connect(self._mark_dirty)
        self.max_context_chars.valueChanged.connect(self._mark_dirty)
        self.persist_conversations.toggled.connect(self._mark_dirty)
        for section in self._sections:
            section.toggle.toggled.connect(self._refresh_section_icons)

        self.setTabOrder(self.back_button, self.provider_combo)
        self.setTabOrder(self.provider_combo, self.model_combo)
        self.setTabOrder(self.model_combo, self.effort_combo)
        self.setTabOrder(self.effort_combo, self.harness_section.toggle)
        self.setTabOrder(self.harness_section.toggle, self.limits_section.toggle)
        self.setTabOrder(self.limits_section.toggle, self.history_section.toggle)
        self.setTabOrder(self.history_section.toggle, self.revert_button)
        self.setTabOrder(self.revert_button, self.apply_button)

    @staticmethod
    def _executable_edit(accessible_name: str, placeholder: str) -> QtWidgets.QLineEdit:
        edit = QtWidgets.QLineEdit()
        edit.setAccessibleName(accessible_name)
        edit.setPlaceholderText(placeholder)
        edit.setClearButtonEnabled(True)
        edit.setMinimumWidth(0)
        return edit

    # -- theming and responsiveness ---------------------------------------

    def _apply_theme(self) -> None:
        palette = self.palette()
        muted = palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        self.back_button.setIcon(branding.glyph_icon("back", muted))
        for widget in self._dim_widgets:
            widget_palette = widget.palette()
            widget_palette.setColor(QtGui.QPalette.ColorRole.WindowText, muted)
            widget.setPalette(widget_palette)
        self._refresh_section_icons()

    def _refresh_section_icons(self, *_args: object) -> None:
        muted = self.palette().color(QtGui.QPalette.ColorRole.PlaceholderText)
        for section in self._sections:
            name = "chevron-down" if section.toggle.isChecked() else "chevron-right"
            section.toggle.setIcon(branding.glyph_icon(name, muted))

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.PaletteChange:
            self._apply_theme()

    def set_narrow(self, narrow: bool) -> None:
        if narrow == self._narrow:
            return
        self._narrow = narrow
        wrap = (
            QtWidgets.QFormLayout.RowWrapPolicy.WrapAllRows
            if narrow
            else QtWidgets.QFormLayout.RowWrapPolicy.DontWrapRows
        )
        self.provider_form.setRowWrapPolicy(wrap)
        for section in self._sections:
            section.set_narrow(narrow)

    # -- state -------------------------------------------------------------

    def load(self) -> None:
        runtime = get_runtime_config()
        preferences = get_sidebar_preferences()
        self._draft_selections = {
            backend: get_provider_selection(backend) for backend in BACKEND_LABELS
        }
        self._active_backend = runtime.provider.backend

        blocker = QtCore.QSignalBlocker(self.provider_combo)
        index = self.provider_combo.findData(self._active_backend)
        self.provider_combo.setCurrentIndex(max(0, index))
        del blocker

        self.populate_provider_options(self._active_backend)
        self.claude_executable.setText(preferences.claude_executable)
        self.codex_executable.setText(preferences.codex_executable)
        self.ollama_executable.setText(preferences.ollama_executable)
        self.timeout_seconds.setValue(preferences.timeout_seconds)
        self.max_context_chars.setValue(preferences.max_context_chars)
        self.persist_conversations.setChecked(preferences.persist_conversations)
        self.refresh_summaries()
        self.status_label.setText("Settings are stored locally in Binary Ninja.")

    def apply(self) -> None:
        self._capture_selection(self._active_backend)
        for backend, (model, effort) in self._draft_selections.items():
            set_provider_selection(backend, model, effort)
        set_backend(self.selected_backend())
        set_sidebar_preferences(
            SidebarPreferences(
                claude_executable=self.claude_executable.text(),
                codex_executable=self.codex_executable.text(),
                ollama_executable=self.ollama_executable.text(),
                timeout_seconds=self.timeout_seconds.value(),
                max_context_chars=self.max_context_chars.value(),
                persist_conversations=self.persist_conversations.isChecked(),
            )
        )
        self.refresh_summaries()
        self.status_label.setText("Settings saved.")
        self.applied.emit()

    def refresh_summaries(self) -> None:
        """Summaries name the executables rather than repeating whole paths."""
        executables = " · ".join(
            (edit.text().strip() or edit.placeholderText())
            .replace("\\", "/")
            .rsplit("/", 1)[-1]
            for edit in (
                self.claude_executable,
                self.codex_executable,
                self.ollama_executable,
            )
        )
        self.harness_section.set_summary(executables)
        self.limits_section.set_summary(
            f"{self.timeout_seconds.value()} s · "
            f"{self.max_context_chars.value():,} chars"
        )
        self.history_section.set_summary(
            "Restoring" if self.persist_conversations.isChecked() else "Off"
        )

    def selected_backend(self) -> str:
        return str(self.provider_combo.currentData() or "claude-code")

    def selected_model(self) -> str:
        index = self.model_combo.currentIndex()
        if (
            index >= 0
            and self.model_combo.currentText() == self.model_combo.itemText(index)
        ):
            return str(self.model_combo.itemData(index) or "")
        return self.model_combo.currentText().strip()

    def selected_effort(self) -> str:
        return str(self.effort_combo.currentData() or "")

    def selected_ollama_executable(self) -> str:
        return self.ollama_executable.text().strip()

    def save_selection(self) -> None:
        self._capture_selection(self._active_backend)

    def populate_provider_options(self, backend: str) -> None:
        model, effort = self._draft_selections.get(
            backend,
            get_provider_selection(backend),
        )
        model_blocker = QtCore.QSignalBlocker(self.model_combo)
        effort_blocker = QtCore.QSignalBlocker(self.effort_combo)

        self.model_combo.clear()
        if backend != "ollama-cloud":
            self.model_combo.addItem("Default (CLI)", "")
        for choice in MODEL_CHOICES[backend]:
            self.model_combo.addItem(choice, choice)
        model_index = self.model_combo.findData(model)
        if model and model_index < 0:
            self.model_combo.addItem(model, model)
            model_index = self.model_combo.count() - 1
        self.model_combo.setCurrentIndex(max(0, model_index))

        self.effort_combo.clear()
        self.effort_combo.addItem("Default (model)", "")
        for choice in REASONING_EFFORTS[backend]:
            self.effort_combo.addItem(choice, choice)
        effort_index = self.effort_combo.findData(effort)
        self.effort_combo.setCurrentIndex(max(0, effort_index))

        del model_blocker
        del effort_blocker
        self.refresh_models_button.setVisible(backend == "ollama-cloud")

    def replace_ollama_models(self, models: list[str]) -> None:
        current = self.selected_model()
        blocker = QtCore.QSignalBlocker(self.model_combo)
        self.model_combo.clear()
        for model in models:
            self.model_combo.addItem(model, model)
        if current and self.model_combo.findData(current) < 0:
            self.model_combo.addItem(current, current)
        selected_index = self.model_combo.findData(current)
        self.model_combo.setCurrentIndex(max(0, selected_index))
        del blocker
        self._capture_selection("ollama-cloud")
        self.selectionChanged.emit()

    def set_busy(self, busy: bool, discovering: bool = False) -> None:
        enabled = not busy
        self.provider_combo.setEnabled(enabled)
        self.model_combo.setEnabled(enabled)
        self.effort_combo.setEnabled(enabled)
        self.claude_executable.setEnabled(enabled)
        self.codex_executable.setEnabled(enabled)
        self.ollama_executable.setEnabled(enabled)
        self.timeout_seconds.setEnabled(enabled)
        self.max_context_chars.setEnabled(enabled)
        self.persist_conversations.setEnabled(enabled)
        self.apply_button.setEnabled(enabled)
        self.revert_button.setEnabled(enabled)
        self.refresh_models_button.setEnabled(enabled and not discovering)

    def set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _provider_changed(self, *_args: object) -> None:
        self._capture_selection(self._active_backend)
        backend = self.selected_backend()
        self._active_backend = backend
        self.populate_provider_options(backend)
        self._mark_dirty()
        self.providerChanged.emit(backend)
        self.selectionChanged.emit()

    def _selection_changed(self, *_args: object) -> None:
        self._capture_selection(self._active_backend)
        self._mark_dirty()
        self.selectionChanged.emit()

    def _request_refresh(self) -> None:
        self.refreshModelsRequested.emit()

    def _capture_selection(self, backend: str) -> None:
        if backend in BACKEND_LABELS:
            self._draft_selections[backend] = (
                self.selected_model(),
                self.selected_effort(),
            )

    def _mark_dirty(self, *_args: object) -> None:
        self.refresh_summaries()
        self.status_label.setText("Unsaved changes.")

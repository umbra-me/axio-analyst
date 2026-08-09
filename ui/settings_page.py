"""Native settings surface for Axio Analyst."""

from PySide6 import QtCore, QtWidgets

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


class SettingsPage(QtWidgets.QWidget):
    applied = QtCore.Signal()
    providerChanged = QtCore.Signal(str)
    refreshModelsRequested = QtCore.Signal()
    selectionChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self._active_backend = "claude-code"
        self._draft_selections: dict[str, tuple[str, str]] = {}
        self._build_interface()
        self.load()

    def _build_interface(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        content = QtWidgets.QWidget()
        content.setMinimumWidth(0)
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(1, 1, 1, 1)
        content_layout.setSpacing(12)

        intro = QtWidgets.QLabel(
            f"Axio Analyst v{VERSION}. Configure local harnesses and request "
            "limits. Credentials remain inside each provider CLI."
        )
        intro.setWordWrap(True)
        content_layout.addWidget(intro)

        provider_group = QtWidgets.QGroupBox("Provider defaults")
        provider_layout = QtWidgets.QFormLayout(provider_group)
        provider_layout.setFieldGrowthPolicy(
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
        model_layout.setSpacing(6)
        model_layout.addWidget(self.model_combo, 1)
        self.refresh_models_button = QtWidgets.QToolButton()
        self.refresh_models_button.setText("Refresh")
        self.refresh_models_button.setToolTip("Fetch available Ollama Cloud models")
        self.refresh_models_button.setAccessibleName("Refresh Ollama Cloud models")
        model_layout.addWidget(self.refresh_models_button)

        self.effort_combo = QtWidgets.QComboBox()
        self.effort_combo.setAccessibleName("Reasoning effort")

        provider_layout.addRow("Provider", self.provider_combo)
        provider_layout.addRow("Model", model_row)
        provider_layout.addRow("Reasoning", self.effort_combo)
        content_layout.addWidget(provider_group)

        harness_group = QtWidgets.QGroupBox("Harness executables")
        harness_layout = QtWidgets.QFormLayout(harness_group)
        harness_layout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.claude_executable = self._executable_edit(
            "Claude Code executable", "claude"
        )
        self.codex_executable = self._executable_edit("Codex executable", "codex")
        self.ollama_executable = self._executable_edit(
            "Ollama executable", "ollama"
        )
        harness_layout.addRow("Claude Code", self.claude_executable)
        harness_layout.addRow("Codex", self.codex_executable)
        harness_layout.addRow("Ollama", self.ollama_executable)
        content_layout.addWidget(harness_group)

        limits_group = QtWidgets.QGroupBox("Request limits")
        limits_layout = QtWidgets.QFormLayout(limits_group)
        limits_layout.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.timeout_seconds = QtWidgets.QSpinBox()
        self.timeout_seconds.setRange(10, 3600)
        self.timeout_seconds.setSingleStep(30)
        self.timeout_seconds.setSuffix(" s")
        self.timeout_seconds.setAccessibleName("Request timeout in seconds")
        self.max_context_chars = QtWidgets.QSpinBox()
        self.max_context_chars.setRange(1000, 500000)
        self.max_context_chars.setSingleStep(5000)
        self.max_context_chars.setSuffix(" chars")
        self.max_context_chars.setAccessibleName("Maximum context characters")
        limits_layout.addRow("Timeout", self.timeout_seconds)
        limits_layout.addRow("HLIL context", self.max_context_chars)
        content_layout.addWidget(limits_group)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAccessibleName("Settings status")
        root.addWidget(self.status_label)

        actions = QtWidgets.QHBoxLayout()
        actions.addStretch(1)
        self.revert_button = QtWidgets.QPushButton("Revert")
        self.revert_button.setToolTip("Reload saved settings")
        self.apply_button = QtWidgets.QPushButton("Apply settings")
        self.apply_button.setDefault(True)
        actions.addWidget(self.revert_button)
        actions.addWidget(self.apply_button)
        root.addLayout(actions)

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

    @staticmethod
    def _executable_edit(accessible_name: str, placeholder: str) -> QtWidgets.QLineEdit:
        edit = QtWidgets.QLineEdit()
        edit.setAccessibleName(accessible_name)
        edit.setPlaceholderText(placeholder)
        edit.setClearButtonEnabled(True)
        edit.setMinimumWidth(0)
        return edit

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
            )
        )
        self.status_label.setText("Settings saved.")
        self.applied.emit()

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
        self.status_label.setText("Unsaved changes.")

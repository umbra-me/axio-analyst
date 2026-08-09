"""Asynchronous Ollama model discovery for the Binary Ninja Qt host."""

import threading

from binaryninja.mainthread import execute_on_main_thread
from PySide6 import QtCore

from ..core.models import ProviderError
from ..providers.ollama import (
    fetch_ollama_cloud_catalog,
    parse_ollama_cloud_models,
)


class OllamaModelDiscovery(QtCore.QObject):
    busyChanged = QtCore.Signal(bool)
    modelsReady = QtCore.Signal(list)
    statusChanged = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self._catalog_loading = False
        self._process: QtCore.QProcess | None = None
        self._executable = "ollama"
        self._alive = True

    @property
    def busy(self) -> bool:
        process_running = (
            self._process is not None
            and self._process.state() != QtCore.QProcess.ProcessState.NotRunning
        )
        return self._catalog_loading or process_running

    def refresh(self, executable: str) -> None:
        if self.busy:
            return
        self._executable = executable
        self._catalog_loading = True
        self.busyChanged.emit(True)
        self.statusChanged.emit("Fetching available Ollama Cloud models...")
        threading.Thread(
            target=self._fetch_catalog,
            name="AxioAnalyst-OllamaCatalog",
            daemon=True,
        ).start()

    def close(self) -> None:
        self._alive = False
        if self._process is not None:
            self._process.kill()

    def _fetch_catalog(self) -> None:
        models: list[str] = []
        error_detail = ""
        try:
            models = fetch_ollama_cloud_catalog()
        except ProviderError as exc:
            error_detail = str(exc)

        try:
            execute_on_main_thread(
                lambda: self._catalog_finished(models, error_detail)
            )
        except Exception:
            pass

    def _catalog_finished(self, models: list[str], error_detail: str) -> None:
        if not self._alive:
            return
        self._catalog_loading = False
        if error_detail:
            self.statusChanged.emit(
                "Remote Ollama catalog unavailable; checking registered models..."
            )
            self._start_registered_models(error_detail)
            return
        if not models:
            self._start_registered_models("the remote catalog contained no models")
            return

        self.modelsReady.emit(models)
        self.statusChanged.emit(
            f"Found {len(models)} available Ollama Cloud model(s)"
        )
        self.busyChanged.emit(False)

    def _start_registered_models(self, remote_error: str) -> None:
        process = QtCore.QProcess(self)
        process.setProgram(self._executable)
        process.setArguments(["list"])
        process.setProcessChannelMode(
            QtCore.QProcess.ProcessChannelMode.SeparateChannels
        )
        process.finished.connect(self._registered_models_finished)
        process.errorOccurred.connect(self._registered_models_error)
        process.setProperty("remoteError", remote_error)
        self._process = process
        self.statusChanged.emit("Checking registered Ollama Cloud models...")
        process.start()

    def _registered_models_finished(self, exit_code: int, *_args: object) -> None:
        process = self._process
        if process is None:
            return
        stdout = bytes(process.readAllStandardOutput()).decode("utf-8", "replace")
        stderr = bytes(process.readAllStandardError()).decode("utf-8", "replace")
        remote_error = str(process.property("remoteError") or "unknown error")
        self._process = None
        process.deleteLater()
        if not self._alive:
            return

        if exit_code != 0:
            detail = stderr.strip() or f"ollama list exited with code {exit_code}"
            self.statusChanged.emit(f"Could not refresh Ollama models: {detail}")
            self.busyChanged.emit(False)
            return

        models = parse_ollama_cloud_models(stdout)
        self.modelsReady.emit(models)
        if models:
            self.statusChanged.emit(
                f"Remote catalog unavailable; found {len(models)} registered "
                "Ollama Cloud model(s)"
            )
        else:
            self.statusChanged.emit(
                "Could not discover Ollama Cloud models. "
                f"Remote: {remote_error}. Type a model name directly."
            )
        self.busyChanged.emit(False)

    def _registered_models_error(self, *_args: object) -> None:
        process = self._process
        if process is None:
            return
        detail = process.errorString()
        self._process = None
        process.deleteLater()
        if not self._alive:
            return
        self.statusChanged.emit(f"Could not start Ollama model discovery: {detail}")
        self.busyChanged.emit(False)

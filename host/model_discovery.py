"""Asynchronous, bounded Ollama discovery for the Binary Ninja Qt host."""

import threading

from binaryninja.mainthread import execute_on_main_thread
from PySide6 import QtCore

from ..core.models import ProviderCancelled, ProviderConfig, ProviderError
from ..providers.ollama import (
    OllamaCloudProvider, fetch_ollama_cloud_catalog, parse_ollama_cloud_models,
)


class _OllamaListProvider(OllamaCloudProvider):
    def command(self) -> list[str]:
        return [self.config.executable, "list"]


class OllamaModelDiscovery(QtCore.QObject):
    busyChanged = QtCore.Signal(bool)
    modelsReady = QtCore.Signal(list)
    statusChanged = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject):
        super().__init__(parent)
        self._catalog_loading = False
        self._registered_loading = False
        self._executable = "ollama"
        self._alive = True
        self._generation = 0
        self._cancelled = threading.Event()

    @property
    def busy(self) -> bool:
        return self._alive and (self._catalog_loading or self._registered_loading)

    def refresh(self, executable: str) -> None:
        if not self._alive:
            return
        if self.busy:
            if executable == self._executable:
                return
            self._cancelled.set()
        self._registered_loading = False
        self._executable = executable
        self._generation += 1
        self._cancelled = threading.Event()
        self._catalog_loading = True
        self.busyChanged.emit(True)
        self.statusChanged.emit("Fetching available Ollama Cloud models...")
        threading.Thread(
            target=self._fetch_catalog, args=(self._generation,),
            name="AxioAnalyst-OllamaCatalog", daemon=True,
        ).start()

    def close(self) -> None:
        self._alive = False
        self._generation += 1
        self._cancelled.set()

    def _dispatch(self, callback, *args) -> None:
        try:
            execute_on_main_thread(lambda: callback(*args))
        except Exception:
            pass  # The host may have shut down.

    def _fetch_catalog(self, generation: int) -> None:
        models: list[str] = []
        error_detail = ""
        try:
            models = fetch_ollama_cloud_catalog()
        except ProviderError as exc:
            error_detail = str(exc)
        self._dispatch(self._catalog_finished, generation, models, error_detail)

    def _catalog_finished(self, generation: int, models: list[str], error_detail: str) -> None:
        if not self._alive or generation != self._generation:
            return
        self._catalog_loading = False
        if error_detail or not models:
            self._registered_loading = True
            self.statusChanged.emit("Remote Ollama catalog unavailable; checking registered models...")
            threading.Thread(
                target=self._fetch_registered_models,
                args=(generation, self._executable, self._cancelled,
                      error_detail or "the remote catalog contained no models"),
                name="AxioAnalyst-OllamaRegisteredModels", daemon=True,
            ).start()
            return
        self.modelsReady.emit(models)
        self.statusChanged.emit(f"Found {len(models)} available Ollama Cloud model(s)")
        self.busyChanged.emit(False)

    def _fetch_registered_models(
        self, generation: int, executable: str, cancelled: threading.Event, remote_error: str,
    ) -> None:
        provider = _OllamaListProvider(ProviderConfig(
            backend="ollama-cloud", executable=executable, model="", timeout_seconds=10,
        ))
        models: list[str] = []
        error_detail = ""
        try:
            output = provider.run_cli("", cancelled.is_set, max_output_bytes=1_000_000)
            models = parse_ollama_cloud_models(output)
        except ProviderCancelled:
            return
        except ProviderError as exc:
            error_detail = str(exc)
        self._dispatch(self._registered_models_finished, generation, models, error_detail, remote_error)

    def _registered_models_finished(
        self, generation: int, models: list[str], error_detail: str, remote_error: str,
    ) -> None:
        if not self._alive or generation != self._generation:
            return
        self._registered_loading = False
        if error_detail:
            self.statusChanged.emit(f"Could not refresh Ollama models: {error_detail}")
        elif models:
            self.modelsReady.emit(models)
            self.statusChanged.emit(
                f"Remote catalog unavailable; found {len(models)} registered Ollama Cloud model(s)"
            )
        else:
            self.modelsReady.emit([])
            self.statusChanged.emit(
                f"Could not discover Ollama Cloud models. Remote: {remote_error}. Type a model name directly."
            )
        self.busyChanged.emit(False)

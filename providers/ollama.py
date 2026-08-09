"""Ollama Cloud CLI adapter and catalog discovery."""

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ..core.models import ProviderError, ProviderResult
from ..core.provider import CancelCheck, StreamCallback
from .process import CliProvider
from .streaming import strip_terminal_sequences

OLLAMA_CLOUD_CATALOG_URL = "https://ollama.com/api/tags"


def parse_ollama_cloud_models(stdout: str) -> list[str]:
    """Extract registered cloud model names from `ollama list` output."""
    models: list[str] = []
    for line in stdout.splitlines():
        columns = line.split()
        if not columns or columns[0].upper() == "NAME":
            continue
        name = columns[0]
        tag = name.rpartition(":")[2]
        if (tag == "cloud" or tag.endswith("-cloud")) and name not in models:
            models.append(name)
    return models


def _ollama_cloud_cli_name(name: str) -> str:
    repository, separator, tag = name.strip().rpartition(":")
    if not separator:
        return f"{name.strip()}:cloud"
    if tag == "cloud" or tag.endswith("-cloud"):
        return name.strip()
    return f"{repository}:{tag}-cloud"


def parse_ollama_cloud_catalog(payload: str) -> list[str]:
    """Convert Ollama's public API model names into local CLI cloud tags."""
    try:
        document: Any = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ProviderError("Ollama returned an invalid cloud catalog.") from exc

    entries = document.get("models") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise ProviderError("Ollama returned an unexpected cloud catalog.")

    models: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name") or entry.get("model")
        if not isinstance(name, str) or not name.strip():
            continue
        cloud_name = _ollama_cloud_cli_name(name)
        if cloud_name not in models:
            models.append(cloud_name)
    return models


def fetch_ollama_cloud_catalog(timeout_seconds: int = 10) -> list[str]:
    """Fetch Ollama's public catalog without depending on Qt networking."""
    request = urllib.request.Request(
        OLLAMA_CLOUD_CATALOG_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "AxioAnalyst/0.7",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read(1_000_001)
    except (OSError, urllib.error.URLError) as exc:
        raise ProviderError(f"Could not fetch the Ollama cloud catalog: {exc}") from exc

    if len(payload) > 1_000_000:
        raise ProviderError("Ollama cloud catalog exceeded the 1 MB safety limit.")
    return parse_ollama_cloud_catalog(payload.decode("utf-8", "replace"))


class OllamaCloudProvider(CliProvider):
    """Run a signed-in Ollama cloud model through the local CLI."""

    @property
    def display_name(self) -> str:
        return "Ollama Cloud"

    def command(self) -> list[str]:
        command = [
            self.config.executable,
            "run",
            self.config.model,
            "--nowordwrap",
            "--hidethinking",
        ]
        if self.config.reasoning_effort:
            command.append(f"--think={self.config.reasoning_effort}")
        return command

    def complete(
        self,
        prompt: str,
        is_cancelled: CancelCheck = None,
        on_stream: StreamCallback = None,
    ) -> ProviderResult:
        if not self.config.executable.strip():
            raise ProviderError("The Ollama executable setting is empty.")
        if not self.config.model.strip():
            raise ProviderError("Choose an Ollama Cloud model before sending.")

        environment = os.environ.copy()
        environment["OLLAMA_NOHISTORY"] = "1"

        def emit(chunk: str) -> None:
            if on_stream is not None:
                clean = strip_terminal_sequences(chunk)
                if clean:
                    on_stream(clean)

        text = strip_terminal_sequences(
            self.run_cli(
                prompt,
                is_cancelled,
                environment,
                on_stdout=emit,
            )
        ).strip()
        if not text:
            raise ProviderError("Ollama Cloud returned no response text.")
        return ProviderResult(
            text=text,
            backend=self.config.backend,
            model=self.config.model,
            reasoning_effort=self.config.reasoning_effort,
        )

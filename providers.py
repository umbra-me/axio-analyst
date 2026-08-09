"""Inference backends.

Backends in this module never import Binary Ninja. Claude Code, Codex, and
Ollama Cloud run as supervised local processes; HTTP and other harnesses can
implement the same Provider interface later.
"""

import codecs
import json
import os
import queue
import re
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from .models import (
    CancelCheck,
    ProviderCancelled,
    ProviderConfig,
    ProviderError,
    ProviderResult,
    StreamCallback,
)

OLLAMA_CLOUD_CATALOG_URL = "https://ollama.com/api/tags"
MAX_PROVIDER_OUTPUT_BYTES = 8_000_000


class Provider(ABC):
    @abstractmethod
    def complete(
        self,
        prompt: str,
        is_cancelled: CancelCheck = None,
        on_stream: StreamCallback = None,
    ) -> ProviderResult:
        raise NotImplementedError


_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def _strip_terminal_sequences(value: str) -> str:
    return _ANSI_ESCAPE.sub("", value)


def _parse_claude_output(stdout: str) -> tuple[str, str]:
    try:
        payload: Any = json.loads(stdout)
    except json.JSONDecodeError:
        payload = []
        for line in stdout.splitlines():
            if not line.strip():
                continue
            try:
                payload.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ProviderError("Claude Code returned invalid JSONL output.") from exc

    if isinstance(payload, list):
        events = payload
        result_events = [
            event
            for event in events
            if isinstance(event, dict) and event.get("type") == "result"
        ]
        if not result_events:
            raise ProviderError("Claude Code returned no result event.")
        payload = result_events[-1]

        model = ""
        for event in events:
            if isinstance(event, dict) and event.get("type") == "system":
                reported = event.get("model")
                if isinstance(reported, str):
                    model = reported
                    break
    elif isinstance(payload, dict):
        model = payload.get("model", "")
    else:
        raise ProviderError("Claude Code returned an unexpected JSON value.")

    if payload.get("is_error") is True:
        detail = payload.get("result") or payload.get("error") or "unknown error"
        raise ProviderError(f"Claude Code failed: {detail}")

    result = payload.get("result")
    if not isinstance(result, str) or not result.strip():
        error = payload.get("error")
        if isinstance(error, str) and error.strip():
            raise ProviderError(f"Claude Code failed: {error.strip()}")
        raise ProviderError("Claude Code returned no result text.")

    clean_model = _strip_terminal_sequences(model).strip() if isinstance(model, str) else ""
    return _strip_terminal_sequences(result).strip(), clean_model


def _claude_stream_delta(event: Any) -> str:
    if not isinstance(event, dict) or event.get("type") != "stream_event":
        return ""
    stream_event = event.get("event")
    if not isinstance(stream_event, dict):
        return ""
    delta = stream_event.get("delta")
    if stream_event.get("type") != "content_block_delta" or not isinstance(
        delta, dict
    ):
        return ""
    text = delta.get("text")
    return text if isinstance(text, str) else ""


def _codex_stream_delta(event: Any) -> str:
    if not isinstance(event, dict) or event.get("type") != "item.completed":
        return ""
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "agent_message":
        return ""
    text = item.get("text")
    return text if isinstance(text, str) else ""


class _JsonLineStream:
    """Decode structured CLI events without assuming pipe chunk boundaries."""

    def __init__(self, extract_text: Any, on_stream: StreamCallback):
        self._extract_text = extract_text
        self._on_stream = on_stream
        self._buffer = ""

    def feed(self, chunk: str) -> None:
        self._buffer += chunk
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._consume(line)

    def finish(self) -> None:
        if self._buffer.strip():
            self._consume(self._buffer)
        self._buffer = ""

    def _consume(self, line: str) -> None:
        if self._on_stream is None or not line.strip():
            return
        try:
            event: Any = json.loads(line)
        except json.JSONDecodeError:
            return
        text = self._extract_text(event)
        if text:
            self._on_stream(_strip_terminal_sequences(text))


def _parse_codex_output(stdout: str) -> str:
    messages: list[str] = []
    errors: list[str] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            event: Any = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProviderError("Codex returned invalid JSONL output.") from exc

        if not isinstance(event, dict):
            continue
        if event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                message = item.get("text")
                if isinstance(message, str) and message.strip():
                    messages.append(message)
        elif event.get("type") in ("error", "turn.failed"):
            detail = event.get("message") or event.get("error")
            if isinstance(detail, str) and detail.strip():
                errors.append(detail.strip())

    if messages:
        return _strip_terminal_sequences(messages[-1]).strip()
    if errors:
        raise ProviderError(f"Codex failed: {errors[-1]}")
    raise ProviderError("Codex returned no final agent message.")


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


class _CliProvider(Provider):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def display_name(self) -> str:
        raise NotImplementedError

    def _run_cli(
        self,
        prompt: str,
        is_cancelled: CancelCheck,
        environment: dict[str, str] | None = None,
        on_stdout: StreamCallback = None,
    ) -> str:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        workdir = os.path.join(tempfile.gettempdir(), "axio-analyst")
        os.makedirs(workdir, exist_ok=True)
        try:
            process = subprocess.Popen(
                self.command(),
                cwd=workdir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                env=environment,
            )
        except FileNotFoundError as exc:
            raise ProviderError(
                f"{self.display_name} executable not found: {self.config.executable}"
            ) from exc
        except OSError as exc:
            raise ProviderError(f"Could not start {self.display_name}: {exc}") from exc

        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        chunks: queue.Queue[tuple[str, bytes | None]] = queue.Queue()

        def pump(channel: str, pipe: Any) -> None:
            read = getattr(pipe, "read1", pipe.read)
            try:
                while True:
                    chunk = read(4096)
                    if not chunk:
                        break
                    chunks.put((channel, chunk))
            except (OSError, ValueError):
                pass
            finally:
                chunks.put((channel, None))

        readers = [
            threading.Thread(
                target=pump,
                args=("stdout", process.stdout),
                name=f"AxioAnalyst-{self.config.backend}-stdout",
                daemon=True,
            ),
            threading.Thread(
                target=pump,
                args=("stderr", process.stderr),
                name=f"AxioAnalyst-{self.config.backend}-stderr",
                daemon=True,
            ),
        ]
        for reader in readers:
            reader.start()

        try:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        except OSError:
            # The exit status and captured stderr provide the useful diagnostic.
            pass

        deadline = time.monotonic() + self.config.timeout_seconds
        decoders = {
            "stdout": codecs.getincrementaldecoder("utf-8")("replace"),
            "stderr": codecs.getincrementaldecoder("utf-8")("replace"),
        }
        output = {"stdout": [], "stderr": []}
        finished_channels: set[str] = set()
        total_bytes = 0

        while len(finished_channels) < 2:
            if is_cancelled is not None and is_cancelled():
                self._stop(process)
                raise ProviderCancelled(f"{self.display_name} request cancelled.")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._stop(process)
                raise ProviderError(
                    f"{self.display_name} timed out after "
                    f"{self.config.timeout_seconds} seconds."
                )

            try:
                channel, chunk = chunks.get(timeout=min(0.1, remaining))
            except queue.Empty:
                continue

            if chunk is None:
                finished_channels.add(channel)
                continue

            total_bytes += len(chunk)
            if total_bytes > MAX_PROVIDER_OUTPUT_BYTES:
                self._stop(process)
                raise ProviderError(
                    f"{self.display_name} exceeded the 8 MB output safety limit."
                )

            text = decoders[channel].decode(chunk)
            output[channel].append(text)
            if channel == "stdout" and text and on_stdout is not None:
                on_stdout(text)

        for channel, decoder in decoders.items():
            tail = decoder.decode(b"", final=True)
            if tail:
                output[channel].append(tail)
                if channel == "stdout" and on_stdout is not None:
                    on_stdout(tail)

        process.wait()
        for reader in readers:
            reader.join(timeout=0.5)
        process.stdout.close()
        process.stderr.close()

        stdout = "".join(output["stdout"])
        stderr = "".join(output["stderr"])

        if process.returncode != 0:
            detail = stderr.strip() or "no diagnostic output on stderr"
            raise ProviderError(
                f"{self.display_name} exited with code {process.returncode}: "
                f"{detail[:2000]}"
            )
        return stdout

    @staticmethod
    def _stop(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe is not None and not pipe.closed:
                pipe.close()


class ClaudeCodeProvider(_CliProvider):
    """Run an already-authenticated Claude Code CLI in print mode."""

    @property
    def display_name(self) -> str:
        return "Claude Code"

    def command(self) -> list[str]:
        command = [
            self.config.executable,
            "-p",
            "--output-format",
            "stream-json",
            "--include-partial-messages",
            "--verbose",
            "--safe-mode",
            "--disable-slash-commands",
            "--no-session-persistence",
            "--permission-mode",
            "dontAsk",
            "--no-chrome",
            "--tools",
            "",
        ]
        if self.config.model:
            command.extend(["--model", self.config.model])
        if self.config.reasoning_effort:
            command.extend(["--effort", self.config.reasoning_effort])
        return command

    def complete(
        self,
        prompt: str,
        is_cancelled: CancelCheck = None,
        on_stream: StreamCallback = None,
    ) -> ProviderResult:
        if not self.config.executable.strip():
            raise ProviderError("The Claude Code executable setting is empty.")
        stream = _JsonLineStream(_claude_stream_delta, on_stream)
        stdout = self._run_cli(prompt, is_cancelled, on_stdout=stream.feed)
        stream.finish()
        text, reported_model = _parse_claude_output(stdout)
        return ProviderResult(
            text=text,
            backend=self.config.backend,
            model=reported_model or self.config.model,
            reasoning_effort=self.config.reasoning_effort,
        )


class CodexCliProvider(_CliProvider):
    """Run an already-authenticated Codex CLI without a persistent session."""

    @property
    def display_name(self) -> str:
        return "Codex"

    def command(self) -> list[str]:
        command = [
            self.config.executable,
            "exec",
            "--json",
            "--color",
            "never",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
        ]
        if self.config.model:
            command.extend(["--model", self.config.model])
        if self.config.reasoning_effort:
            command.extend(
                [
                    "--config",
                    f'model_reasoning_effort="{self.config.reasoning_effort}"',
                ]
            )
        command.append("-")
        return command

    def complete(
        self,
        prompt: str,
        is_cancelled: CancelCheck = None,
        on_stream: StreamCallback = None,
    ) -> ProviderResult:
        if not self.config.executable.strip():
            raise ProviderError("The Codex executable setting is empty.")
        stream = _JsonLineStream(_codex_stream_delta, on_stream)
        stdout = self._run_cli(prompt, is_cancelled, on_stdout=stream.feed)
        stream.finish()
        return ProviderResult(
            text=_parse_codex_output(stdout),
            backend=self.config.backend,
            model=self.config.model,
            reasoning_effort=self.config.reasoning_effort,
        )


class OllamaCloudProvider(_CliProvider):
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
                clean = _strip_terminal_sequences(chunk)
                if clean:
                    on_stream(clean)

        text = _strip_terminal_sequences(
            self._run_cli(
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


def create_provider(config: ProviderConfig) -> Provider:
    if config.backend == "claude-code":
        return ClaudeCodeProvider(config)
    if config.backend == "codex-cli":
        return CodexCliProvider(config)
    if config.backend == "ollama-cloud":
        return OllamaCloudProvider(config)
    raise ProviderError(f"Unsupported Axio Analyst backend: {config.backend}")

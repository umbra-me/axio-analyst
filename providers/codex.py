"""Codex CLI adapter and event parsing."""

import json
from typing import Any

from ..core.models import ProviderError, ProviderResult
from ..core.provider import CancelCheck, StreamCallback
from .process import CliProvider
from .streaming import JsonLineStream, strip_terminal_sequences


def codex_stream_delta(event: Any) -> str:
    if not isinstance(event, dict) or event.get("type") != "item.completed":
        return ""
    item = event.get("item")
    if not isinstance(item, dict) or item.get("type") != "agent_message":
        return ""
    text = item.get("text")
    return text if isinstance(text, str) else ""


def parse_codex_output(stdout: str) -> str:
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
        return strip_terminal_sequences(messages[-1]).strip()
    if errors:
        raise ProviderError(f"Codex failed: {errors[-1]}")
    raise ProviderError("Codex returned no final agent message.")


class CodexCliProvider(CliProvider):
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
        stream = JsonLineStream(codex_stream_delta, on_stream)
        stdout = self.run_cli(prompt, is_cancelled, on_stdout=stream.feed)
        stream.finish()
        return ProviderResult(
            text=parse_codex_output(stdout),
            backend=self.config.backend,
            model=self.config.model,
            reasoning_effort=self.config.reasoning_effort,
        )

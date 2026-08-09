"""Claude Code CLI adapter and event parsing."""

import json
from typing import Any

from ..core.models import ProviderError, ProviderResult
from ..core.provider import CancelCheck, StreamCallback
from .process import CliProvider
from .streaming import JsonLineStream, strip_terminal_sequences


def parse_claude_output(stdout: str) -> tuple[str, str]:
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

    clean_model = (
        strip_terminal_sequences(model).strip() if isinstance(model, str) else ""
    )
    return strip_terminal_sequences(result).strip(), clean_model


def claude_stream_delta(event: Any) -> str:
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


class ClaudeCodeProvider(CliProvider):
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
        stream = JsonLineStream(claude_stream_delta, on_stream)
        stdout = self.run_cli(prompt, is_cancelled, on_stdout=stream.feed)
        stream.finish()
        text, reported_model = parse_claude_output(stdout)
        return ProviderResult(
            text=text,
            backend=self.config.backend,
            model=reported_model or self.config.model,
            reasoning_effort=self.config.reasoning_effort,
        )

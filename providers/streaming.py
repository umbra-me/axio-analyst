"""Streaming helpers shared by structured CLI adapters."""

import json
import re
from typing import Any

from ..core.provider import StreamCallback

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_terminal_sequences(value: str) -> str:
    return _ANSI_ESCAPE.sub("", value)


class JsonLineStream:
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
            self._on_stream(strip_terminal_sequences(text))

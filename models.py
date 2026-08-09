"""Provider-neutral request and response types for Axio Analyst."""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class FunctionContext:
    binary_name: str
    function_name: str
    function_start: int
    architecture: str
    platform: str
    function_type: str
    hlil: str
    truncated: bool = False


@dataclass(frozen=True)
class ProviderConfig:
    backend: str
    executable: str
    model: str
    timeout_seconds: int
    reasoning_effort: str = ""


@dataclass(frozen=True)
class ProviderResult:
    text: str
    backend: str
    model: str = ""
    reasoning_effort: str = ""


CancelCheck = Optional[Callable[[], bool]]
StreamCallback = Optional[Callable[[str], None]]


class ProviderError(RuntimeError):
    """A provider could not complete a request."""


class ProviderCancelled(ProviderError):
    """The user cancelled a provider request."""

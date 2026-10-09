"""Provider-neutral request, response, and context types for Axio Analyst."""

from dataclasses import dataclass, field
from typing import Optional


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
class ContextOptions:
    include_selection: bool = False
    include_callers: bool = False
    include_callees: bool = False
    include_strings: bool = False
    include_imports: bool = False
    include_types: bool = False
    max_callers: int = 3
    max_callees: int = 5
    max_strings: int = 20
    max_imports: int = 20


@dataclass(frozen=True)
class ContextItem:
    kind: str
    label: str
    text: str
    start_address: Optional[int] = None
    end_address: Optional[int] = None
    truncated: bool = False

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class ContextBundle:
    primary: FunctionContext
    items: tuple[ContextItem, ...]
    max_chars: int
    truncated: bool = False

    @property
    def total_chars(self) -> int:
        return sum(item.char_count for item in self.items)

    @property
    def evidence_addresses(self) -> tuple[int, ...]:
        addresses = {
            address
            for item in self.items
            for address in (item.start_address, item.end_address)
            if address is not None
        }
        return tuple(sorted(addresses))


@dataclass(frozen=True)
class ProviderConfig:
    backend: str
    executable: str
    model: str
    timeout_seconds: int
    reasoning_effort: str = ""


@dataclass(frozen=True)
class ProviderUsage:
    input_chars: int = 0
    output_chars: int = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    duration_seconds: float = 0.0


@dataclass(frozen=True)
class ProviderResult:
    text: str
    backend: str
    model: str = ""
    reasoning_effort: str = ""
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    error: str = ""
    cancelled: bool = False


class ProviderError(RuntimeError):
    """A provider could not complete a request."""


class ProviderCancelled(ProviderError):
    """The user cancelled a provider request."""

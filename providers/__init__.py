"""Provider adapters and factory."""

from ..core.models import ProviderConfig, ProviderError
from ..core.provider import Provider
from .claude import (
    ClaudeCodeProvider,
    claude_stream_delta,
    parse_claude_output,
    parse_claude_response,
)
from .codex import (
    CodexCliProvider,
    codex_stream_delta,
    parse_codex_output,
    parse_codex_response,
)
from .ollama import (
    OllamaCloudProvider,
    fetch_ollama_cloud_catalog,
    parse_ollama_cloud_catalog,
    parse_ollama_cloud_models,
)
from .process import CliProvider
from .streaming import JsonLineStream


def create_provider(config: ProviderConfig) -> Provider:
    if config.backend == "claude-code":
        return ClaudeCodeProvider(config)
    if config.backend == "codex-cli":
        return CodexCliProvider(config)
    if config.backend == "ollama-cloud":
        return OllamaCloudProvider(config)
    raise ProviderError(f"Unsupported Axio Analyst backend: {config.backend}")


__all__ = [
    "ClaudeCodeProvider",
    "CliProvider",
    "CodexCliProvider",
    "JsonLineStream",
    "OllamaCloudProvider",
    "claude_stream_delta",
    "codex_stream_delta",
    "create_provider",
    "fetch_ollama_cloud_catalog",
    "parse_claude_output",
    "parse_claude_response",
    "parse_codex_output",
    "parse_codex_response",
    "parse_ollama_cloud_catalog",
    "parse_ollama_cloud_models",
]

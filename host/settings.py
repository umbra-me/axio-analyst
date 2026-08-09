"""Binary Ninja settings registration for Axio Analyst."""

import json
from dataclasses import dataclass

from binaryninja import Settings

from ..core.models import ProviderConfig

GROUP = "axioAnalyst"
_IGNORE_DATABASE_SCOPES = ["SettingsProjectScope", "SettingsResourceScope"]
BACKEND_LABELS = {
    "claude-code": "Claude Code",
    "codex-cli": "Codex",
    "ollama-cloud": "Ollama Cloud",
}
MODEL_CHOICES = {
    "claude-code": ["opus", "sonnet", "fable"],
    "codex-cli": [
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "gpt-5.5",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.2",
    ],
    "ollama-cloud": [],
}
REASONING_EFFORTS = {
    "claude-code": ["low", "medium", "high", "xhigh", "max"],
    "codex-cli": ["low", "medium", "high", "xhigh", "max", "ultra"],
    "ollama-cloud": ["low", "medium", "high"],
}
_PROVIDER_PREFIXES = {
    "claude-code": "claudeCode",
    "codex-cli": "codex",
    "ollama-cloud": "ollamaCloud",
}


@dataclass(frozen=True)
class RuntimeConfig:
    provider: ProviderConfig
    max_context_chars: int
    persist_conversations: bool


@dataclass(frozen=True)
class SidebarPreferences:
    claude_executable: str
    codex_executable: str
    ollama_executable: str
    timeout_seconds: int
    max_context_chars: int
    persist_conversations: bool


def _register(key: str, **properties: object) -> None:
    properties["ignore"] = _IGNORE_DATABASE_SCOPES
    Settings().register_setting(f"{GROUP}.{key}", json.dumps(properties))


def register_settings() -> None:
    settings = Settings()
    settings.register_group(GROUP, "Axio Analyst")

    _register(
        "backend",
        title="Backend",
        description="Provider or local harness used for analysis requests.",
        type="string",
        default="claude-code",
        enum=["claude-code", "codex-cli", "ollama-cloud"],
        enumDescriptions=[
            "Claude Code (headless -p)",
            "Codex (headless exec)",
            "Ollama Cloud (authenticated CLI)",
        ],
    )
    _register(
        "claudeCode.executable",
        title="Claude Code Executable",
        description="Executable name or absolute path for the Claude Code CLI.",
        type="string",
        default="claude",
    )
    _register(
        "claudeCode.model",
        title="Claude Code Model",
        description="Optional model alias or full model name. Empty uses the CLI default.",
        type="string",
        default="",
    )
    _register(
        "claudeCode.reasoningEffort",
        title="Claude Code Reasoning Effort",
        description="Optional effort override. Empty uses the CLI/model default.",
        type="string",
        default="",
    )
    _register(
        "codex.executable",
        title="Codex Executable",
        description="Executable name or absolute path for the Codex CLI.",
        type="string",
        default="codex",
    )
    _register(
        "codex.model",
        title="Codex Model",
        description="Optional model name. Empty uses the CLI default.",
        type="string",
        default="",
    )
    _register(
        "codex.reasoningEffort",
        title="Codex Reasoning Effort",
        description="Optional effort override. Empty uses the CLI/model default.",
        type="string",
        default="",
    )
    _register(
        "ollamaCloud.executable",
        title="Ollama Executable",
        description="Executable name or absolute path for the Ollama CLI.",
        type="string",
        default="ollama",
    )
    _register(
        "ollamaCloud.model",
        title="Ollama Cloud Model",
        description="Cloud model name passed to ollama run.",
        type="string",
        default="gpt-oss:120b-cloud",
    )
    _register(
        "ollamaCloud.reasoningEffort",
        title="Ollama Cloud Thinking Level",
        description="Optional thinking level. Empty uses the model default.",
        type="string",
        default="",
    )
    _register(
        "timeoutSeconds",
        title="Request Timeout (seconds)",
        description="Maximum time allowed for one provider request.",
        type="number",
        default=300,
        minValue=10,
        maxValue=3600,
    )
    _register(
        "maxContextChars",
        title="Maximum Context Characters",
        description="Maximum HLIL characters included in a single request.",
        type="number",
        default=60000,
        minValue=1000,
        maxValue=500000,
    )
    _register(
        "persistConversations",
        title="Persist Conversations",
        description=(
            "Store bounded transcripts in the Binary Ninja user directory, "
            "keyed by a path-free binary fingerprint."
        ),
        type="boolean",
        default=False,
    )


def get_provider_selection(backend: str) -> tuple[str, str]:
    prefix = _PROVIDER_PREFIXES.get(backend, "claudeCode")
    settings = Settings()
    return (
        settings.get_string(f"{GROUP}.{prefix}.model"),
        settings.get_string(f"{GROUP}.{prefix}.reasoningEffort"),
    )


def set_provider_selection(backend: str, model: str, reasoning_effort: str) -> None:
    if backend not in _PROVIDER_PREFIXES:
        return
    prefix = _PROVIDER_PREFIXES[backend]
    settings = Settings()
    settings.set_string(f"{GROUP}.{prefix}.model", model)
    settings.set_string(f"{GROUP}.{prefix}.reasoningEffort", reasoning_effort)


def set_backend(backend: str) -> None:
    if backend in _PROVIDER_PREFIXES:
        Settings().set_string(f"{GROUP}.backend", backend)


def get_sidebar_preferences() -> SidebarPreferences:
    settings = Settings()
    return SidebarPreferences(
        claude_executable=settings.get_string(f"{GROUP}.claudeCode.executable"),
        codex_executable=settings.get_string(f"{GROUP}.codex.executable"),
        ollama_executable=settings.get_string(f"{GROUP}.ollamaCloud.executable"),
        timeout_seconds=settings.get_integer(f"{GROUP}.timeoutSeconds"),
        max_context_chars=settings.get_integer(f"{GROUP}.maxContextChars"),
        persist_conversations=settings.get_bool(
            f"{GROUP}.persistConversations"
        ),
    )


def set_sidebar_preferences(preferences: SidebarPreferences) -> None:
    settings = Settings()
    settings.set_string(
        f"{GROUP}.claudeCode.executable",
        preferences.claude_executable.strip(),
    )
    settings.set_string(
        f"{GROUP}.codex.executable",
        preferences.codex_executable.strip(),
    )
    settings.set_string(
        f"{GROUP}.ollamaCloud.executable",
        preferences.ollama_executable.strip(),
    )
    settings.set_integer(
        f"{GROUP}.timeoutSeconds",
        max(10, min(3600, preferences.timeout_seconds)),
    )
    settings.set_integer(
        f"{GROUP}.maxContextChars",
        max(1000, min(500000, preferences.max_context_chars)),
    )
    settings.set_bool(
        f"{GROUP}.persistConversations",
        preferences.persist_conversations,
    )


def get_provider_config(backend: str) -> ProviderConfig:
    settings = Settings()
    prefix = _PROVIDER_PREFIXES.get(backend)
    if prefix is None:
        raise ValueError(f"Unsupported provider backend: {backend}")
    return ProviderConfig(
        backend=backend,
        executable=settings.get_string(f"{GROUP}.{prefix}.executable"),
        model=settings.get_string(f"{GROUP}.{prefix}.model"),
        timeout_seconds=settings.get_integer(f"{GROUP}.timeoutSeconds"),
        reasoning_effort=settings.get_string(f"{GROUP}.{prefix}.reasoningEffort"),
    )


def get_runtime_config() -> RuntimeConfig:
    settings = Settings()
    backend = settings.get_string(f"{GROUP}.backend")
    return RuntimeConfig(
        provider=get_provider_config(backend),
        max_context_chars=settings.get_integer(f"{GROUP}.maxContextChars"),
        persist_conversations=settings.get_bool(
            f"{GROUP}.persistConversations"
        ),
    )

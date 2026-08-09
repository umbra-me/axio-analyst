# Changelog

All notable product changes are recorded here. Axio Analyst is pre-release;
interfaces, settings, and storage decisions may change before `1.0.0`, but
breaking changes must still be documented with migration instructions.

## Unreleased

### Added

- Publish the standalone Axio Analyst repository with complete setup,
  configuration, provider, architecture, development, troubleshooting, and
  handoff documentation.
- Add a documentation ownership index and a manual Binary Ninja GUI checklist.

### Changed

- Standardize the product, package, plugin directory, settings namespace,
  tests, sample, temporary work directory, and sidebar icon on Axio Analyst
  naming.
- Establish the standalone repository as the product source of truth; the
  personal Binary Ninja configuration repository is only a local mirror.

## 0.7.0 - 2026-08-08

### Added

- Native right-sidebar Chat and Settings pages.
- Cursor-following current-function context and one-shot plugin commands.
- Provider-neutral Claude Code, Codex, and Ollama Cloud adapters.
- Editable model selection and provider-specific reasoning effort.
- Bounded address-labelled HLIL prompts with explicit truncation disclosure.
- Streamed Claude Code and Ollama output and Codex lifecycle/final-message
  handling.
- Background stdout/stderr readers, timeout enforcement, cancellation, elapsed
  time, and phase progress.
- Sanitized Markdown rendering with raw-HTML escaping and stable manual scroll
  position.
- Asynchronous Ollama public-cloud catalog discovery with `ollama list`
  fallback and editable manual model entry.
- Stock-Python tests, a bounded development installer, and a C++ reversing
  fixture.

### Security

- Send prompts through stdin rather than process arguments.
- Disable Claude tools/session persistence and run Codex ephemerally in a
  read-only sandbox with user rules/configuration ignored.
- Disable Ollama prompt history for the child process.
- Limit requests to the selected function's metadata and bounded HLIL.
- Keep the release read-only with no BNDB mutations.

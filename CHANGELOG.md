# Changelog

All notable product changes are recorded here. Axio Analyst is pre-release;
interfaces, settings, and storage decisions may change before `1.0.0`, but
breaking changes must still be documented with migration instructions.

## Unreleased

## 0.9.0 - 2026-08-10

### Added

- Add an exact context preview with a frozen request snapshot, item/character
  totals, and visible truncation state.
- Add opt-in current-selection, direct caller/callee, referenced string/import,
  and relevant-function-type context packs with conservative item caps.
- Add validated address evidence links that navigate inside Binary Ninja while
  leaving invalid citations and generic provider links inert.
- Add optional machine-local conversation restoration with a versioned bounded
  JSON schema, path-free sampled content fingerprint, atomic replacement,
  explicit deletion, and Markdown export.
- Add qualitative comparison between the active provider and one alternative
  using the same frozen context snapshot.
- Add normalized latency and character accounting, Claude token/cache/cost
  extraction, and Codex token/cache extraction.

### Changed

- Rework the native sidebar around a dominant transcript and compact composer,
  with a dedicated context workspace, on-demand comparison, and one shared
  Ask/Stop action position.
- Open completed provider responses at their beginning instead of leaving long
  answers parked at the final lines.
- Reflow Settings form rows when the Binary Ninja dock is narrow.
- Replace the one-function prompt model with an ordered, deduplicated
  `ContextBundle` under one deterministic total character budget.
- Reserve context capacity for explicitly enabled neighbour packs and limit
  each rendered neighbour so one function cannot consume the full request.
- Show provider-specific output and usage summaries in comparison responses.
- Bump all Binary Ninja version surfaces and distribution metadata to `0.9.0`.
- Document the current Binary Ninja Sidekick capability surface, service and
  offline boundaries, permissions, storage, privacy, automation, limitations,
  and implications for Axio Analyst.

### Security

- Keep every additional context pack opt-in and expose the exact provider-bound
  text before dispatch without including a source path or whole binary.
- Keep persistence off by default, cap records at 200 messages and 8 MB, reject
  unsafe identifiers and unknown schemas, and keep credentials/context snapshots
  out of the record.
- Validate provider-supplied address citations against the active BinaryView
  before constructing an internal navigation action.
- Preserve the read-only BNDB boundary and all supervised CLI restrictions.

## 0.8.0 - 2026-08-09

### Added

- Publish the standalone Axio Analyst repository with complete setup,
  configuration, provider, architecture, development, troubleshooting, and
  handoff documentation.
- Add a documentation ownership index and a manual Binary Ninja GUI checklist.
- Add a validated semantic-version source backed by `plugin.json`, plus version
  display in the sidebar, Settings page, log, and About command.

### Changed

- Standardize the product, package, plugin directory, settings namespace,
  tests, sample, temporary work directory, and sidebar icon on Axio Analyst
  naming.
- Establish the standalone repository as the product source of truth; the
  personal Binary Ninja configuration repository is only a local mirror.
- Separate provider-neutral core and application logic, provider adapters,
  Binary Ninja host integration, and Qt presentation into explicit packages.
- Split provider, process, prompt, rendering, application, and distribution
  tests so the test tree mirrors the runtime boundaries.
- Teach the development installer to detect obsolete flat-layout modules and
  optionally remove only that explicit migration allowlist.

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

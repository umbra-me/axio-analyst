# Changelog

All notable product changes are recorded here. Axio Analyst is pre-release;
interfaces, settings, and storage decisions may change before `1.0.0`, but
breaking changes must still be documented with migration instructions.

## Unreleased

- September 5: Unverified structured findings, context provenance and schema-2 transcript persistence/export with schema-1 compatibility. See [change set](docs/change-set-2026-09-05.md).

### Added

- Add `samples/demo/build.sh`, the macOS and Linux counterpart of `build.ps1`:
  a native Release build of the same fixture through CMake, Ninja when present,
  with the executable directly under `build/`. Verified on Apple Silicon: the
  `--demo` output matches the Windows build byte for byte and all eight named
  functions survive as symbols.
- Add a dated real-host GUI verification report covering registration, the
  redesigned resting layout, function tracking, context previews, Settings,
  read-only evidence, the provider-authorisation boundary, and Binary Ninja's
  built-in confirmation that binaries are positional arguments while
  `-l, --debug-log <file>` names a log destination.
- Document safe recovery for Binary Ninja's application-level **Updater is not
  valid** error separately from Axio Analyst installation and runtime failures.
- Add `ui/branding.py`: an original painted Axio Analyst mark - a split diamond
  standing for one bounded context read more than one way - plus a thirteen
  glyph action set drawn in one stroke language on a shared 24-unit grid. The
  artwork is painted from the active Qt palette rather than shipped as an
  asset, so it stays crisp at any dock scale, follows light and dark Binary
  Ninja themes, and adds no file for the development installer to package.

### Changed

- Replace the programmatically drawn `AX` text monogram used as the sidebar
  icon with the painted mark.
- Reduce the resting chat surface to two bands: one header row and one
  composer. The context card, transcript frame, detail row, action row, and
  permanent status strip are all gone.
- Merge the composer into a single control carrying the prompt, the scope chip,
  the keyboard hint, and the send action, which becomes **Stop** in place while
  a request runs.
- Replace the greeting message with an empty state naming the function, its
  architecture, and the configured provider above four suggested questions, so
  the conversation starts genuinely empty and **Explain** is discoverable
  without a permanent button.
- Move **Explain this function**, **Compare with**, **Export conversation**,
  **Clear conversation**, and the installed version into the header overflow
  menu.
- Move the scope disclosure onto the composer's chip, which names the function
  and appends `+N` for opt-in packs, eliding the name rather than the count on
  a narrow dock.
- Reveal the status line only while it has something to report, then hide it
  again; progress becomes a two-pixel line above the composer.
- Collapse each answer's role metadata, evidence links, and unresolved-citation
  disclosure from up to four separate lines onto one footer line.
- Replace the four Settings group boxes with flat sections; Executables,
  Request limits, and Local history collapse behind one-line summaries of their
  staged values.
- Stack Settings form labels above their fields on a narrow dock and reserve
  height for wrapped label text so guidance is no longer clipped.

### Fixed

- Render fenced code blocks correctly. Escaping the provider string before the
  Markdown import leaked `&gt;`, `&lt;`, and `&amp;` into every code block,
  because CommonMark does not decode entities inside code.
- Stop long code blocks from scrolling the whole transcript sideways at
  realistic dock widths by letting imported code blocks wrap; they now also
  render on a background card.

### Security

- Neutralise raw provider HTML at the parser instead of in the source string:
  the transcript imports with `QTextDocument.MarkdownNoHTML`, so md4c never
  emits an HTML block or span and a provider tag can only appear as inert
  literal text. This is a strictly stronger control than escaping and is
  covered by a distribution contract test.

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

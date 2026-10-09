# Changelog

All notable product changes are recorded here. Axio Analyst is pre-release;
interfaces, settings, and storage decisions may change before `1.0.0`, but
breaking changes must still be documented with migration instructions.

## Unreleased

No additional changes recorded.

## 0.9.1 - pending release

Version selected on October 10 for the accumulated changes below. This is a
prepared source candidate, not a tagged or published release. The actual release
date remains pending acceptance and publication approval. See the
[release notes draft](docs/release-notes-draft.md) and
[release preparation](docs/release-preparation.md) for verification evidence,
open gates, and future tag/push commands.
- October 9 presentation draft: Put the README pitch, quick start, and features
  first; summarize the security model; add pending real screenshot/GIF slots
  and a [capture plan](docs/capture-plan.md). Align the maintainer and copyright
  with Kian (Zenco), without claiming new GUI results.
- October 9: Release-readiness source fixes and regression coverage, without a
  version bump or new live GUI receipt. See the [change set](docs/change-set-2026-10-09.md)
  for completed source checks and remaining confinement/platform/host gates.
- September 5: Unverified structured findings, context provenance and schema-2 transcript persistence/export with schema-1 compatibility. See [change set](docs/change-set-2026-09-05.md).

### Added

- Add a community-submission requirements audit, unsent issue text, and three
  public walkthrough candidates with unfilled result slots. Add a distribution
  contract for metadata field limits, enums, build type, and license parity.
- Add POSIX process-group and Windows kill-on-close Job Object cleanup using
  only the Python standard library; Windows behavior still requires validation.
- Add harmless-child lifecycle tests, host-fake callback/context/discovery tests,
  and optional native Qt transcript tests using Binary Ninja's existing bundle.
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

- Shorten plugin-manager description to 43 characters, satisfying both legacy
  under-50 guidance and the current validator's limit. Preserve the advertised
  build/platform fields as unverified compatibility gates pending live checks.
- Keep streamed output as raw chunks, insert a literal live preview capped at
  64,000 characters with a visible notice, and render canonical Markdown once
  at completion, failure, or cancellation.
- Give each CLI run a unique temporary working directory, bounded reader queue,
  and cleanup on success and all failure paths.
- Run `ollama list` discovery through the shared supervisor with a 10-second
  deadline and 1 MB output cap, superseding old discovery when its executable
  changes.
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

- Keep timeout/cancellation checks active while stdin is blocked and after
  output pipes close; attempt kill/wait even when graceful cleanup fails.
- Reject Codex turns containing `error`/`turn.failed` or lacking
  `turn.completed`, including turns that emit an agent message first.
- Reject late analysis/preview callbacks after binary replacement, settings
  changes, or request supersession; retain the correct binary for navigation
  and persistence.
- Bound lazy HLIL extraction and candidate searches, expose truncation when
  searches exhaust their limits, and slice string/import values before decode.
- Share the same deduplicated three-caller/five-callee selection between
  neighbourhood context and relevant types.
- Preserve completed primary findings and usage when secondary comparison
  work is cancelled.
- Render fenced code blocks correctly. Escaping the provider string before the
  Markdown import leaked `&gt;`, `&lt;`, and `&amp;` into every code block,
  because CommonMark does not decode entities inside code.
- Stop long code blocks from scrolling the whole transcript sideways at
  realistic dock widths by letting imported code blocks wrap; they now also
  render on a background card.

### Security

- Disable Codex shell/image tools and web search explicitly. Snapshot-only
  confidentiality remains unproven: independent tool registration and readable
  local files remain an open release gate, documented in the provider contract.
- Document process-tree containment limits, sampled conversation-identity
  aliases, and the unverified Markdown image/resource-loading policy.
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

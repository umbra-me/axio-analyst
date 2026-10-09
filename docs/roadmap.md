# Axio Analyst roadmap

Current source fixes and verification gates are recorded in
[the October 9 change set](change-set-2026-10-09.md). The
[September 5 change set](change-set-2026-09-05.md) retains earlier structured
findings and live receipts; those observations do not verify the October fixes.

The current architecture and security boundaries are documented in
[architecture.md](architecture.md). This document owns future product scope so
aspirational behavior is not confused with the implemented release.

The dated [Sidekick capability inventory](sidekick-capability-inventory.md)
documents the external reference product behind several long-term workflow
ideas. It is research input, not an Axio Analyst compatibility commitment.

## Product end state

Axio Analyst should support six connected workflows:

1. **Ask and investigate** - chat about a selection, function, subsystem, or
   whole binary while bounded agents gather context through explicit tools.
2. **Improve decompilation** - propose names, types, structures, comments, and
   control-flow cleanups; preview every change and apply it as one undoable
   transaction.
3. **Search and index** - build local lexical and semantic indexes over
   functions, strings, imports, types, and findings, with source addresses on
   every result.
4. **Preserve knowledge** - keep conversations, findings, evidence, open
   questions, and rejected hypotheses beside the BNDB in a portable workspace.
5. **Map and verify** - render call/data-flow maps and attach claims to IL,
   assembly, memory, debugger observations, or other reproducible evidence.
6. **Automate safely** - run reusable prompts, scripts, MCP tools, and agent
   workflows with per-tool permissions, budgets, cancellation, and a trace.

The eventual UI is a dockable workspace with chat, context preview, findings,
proposed changes, provider status, token/cost accounting, and request traces.
Menu commands remain available for fast one-shot actions.

## Phases 0-1 - read-only daily assistant

The user-facing analysis workflow landed in `0.7.0`; `0.8.0` retained that
read-only behavior while separating package boundaries, splitting the test
tree, adding manifest-aware migration, and exposing one validated version
through Binary Ninja. Version `0.9.0` adds the transparent daily-assistant
features without crossing the BNDB mutation or credential boundaries.

Implemented in the current `0.9.0` source, including Unreleased changes:

- Explain or ask about the current function.
- Address-labelled current-function HLIL plus opt-in selection, direct
  caller/callee, referenced string/import, and relevant-type packs.
- Exact context preview, stable ordering/deduplication, per-neighbour caps, and
  one configurable combined character budget.
- Provider-neutral Claude Code, Codex, and Ollama Cloud CLI adapters.
- Background execution, timeout, cancellation, safety flags, and no BNDB
  modification.
- A native sidebar whose resting layout is one header row and one composer,
  with a suggestion-led empty state, a self-hiding status line, a
  progressively disclosed Settings surface, an original painted product mark,
  and a shared action-glyph set.
- Bounded literal-text streaming previews followed by HTML-disabled terminal
  Markdown, wrapped code blocks, progress, elapsed time, and optional bounded
  local transcript restoration, deletion, and Markdown export.
- Validated internal navigation for address citations, with unresolved-address
  disclosure and no generic external-link opening.
- Optional two-provider comparison using one frozen context snapshot.
- Normalized duration/character usage, Claude token/cache/cost metadata, and
  Codex token/cache metadata when their JSON events expose it.
- Non-blocking Ollama catalog discovery with local registered-model fallback.
- Explicit `core/`, `application/`, `providers/`, `host/`, and `ui/` boundaries
  with stock-Python dependency contracts.
- Semantic-version visibility in plugin metadata, sidebar, Settings, About,
  and log surfaces.
- A nested-runtime installer that detects drift and can prune only known
  obsolete flat-layout modules.

### Current limitations

- Model suggestions do not guarantee account access.
- Context packs remain a direct bounded neighbourhood, not a recursive or
  whole-program investigation/index.
- Findings carry bounded claims, cited addresses, supplied excerpts, context
  hashes, and provider metadata with explicit unverified status. Claim
  adjudication, automatic stale-state UI, and a provenance graph remain future work.
- Local transcript persistence is intentionally machine-local, off by default,
  and not a portable collaborative workspace.
- Ollama CLI output does not expose token or cost accounting through this
  adapter; cost is shown only when the provider reports it.
- Provider comparison runs the primary then comparison adapter sequentially;
  it is not a benchmark harness or statistical evaluator.
- The one-line answer footer still wraps on a dock narrower than roughly 300
  pixels, because the usage summary reports latency, characters, and tokens in
  full. Shortening it is a product decision about how much accounting belongs
  inline rather than behind a detail surface.
- There is no proposed Binary Ninja transaction schema.
- Codex exposes completed agent messages rather than token-level deltas.
- Codex snapshot-only filesystem/tool confinement is not established by its
  current flags; [the provider contract](providers.md#codex) records the open gate.
- Source tests do not establish live Binary Ninja acceptance, Windows process
  cleanup, or a Markdown image/resource-loading policy. Sampled conversation
  fingerprints can alias binaries differing outside sampled regions.

## Remaining Phase 1 work

- OpenAI-compatible and Anthropic API adapters.
- Environment/credential-store API keys and an OAuth token broker.
- Verified claim adjudication and a provenance graph beyond the implemented
  unverified finding records.
- Portable workspace import/export with explicit migration and retention
  controls. Credentials remain outside every workspace schema.
- Provider-specific cost configuration where the CLI does not report cost.

## Phase 2 - reversible transformations

- Rename, retype, comment, and structure suggestions as a reviewable diff.
- Validate addresses and object identities against current analysis state.
- Apply accepted changes in one undo action and record the transaction.
- Persistent notebook, findings, and rejected hypotheses.

## Phase 3 - agentic investigation

- Read-only Binary Ninja tool broker and MCP surface.
- Bounded multi-step investigations with turn, time, context, and cost budgets.
- Semantic indexes and evidence-aware search.
- Repeatable skills and workflows with inspectable traces.

Headless coding harnesses must not receive filesystem or shell access merely
because they support it. Tool access goes through a narrow allowlisted broker
with request-scoped permissions, timeouts, and cancellation.

## Phase 4 - workspace intelligence

- Cross-binary projects, code/data-flow maps, debugger evidence, and stale
  finding invalidation.
- Import/export and collaboration without coupling analysis data to a provider.
- Evaluation fixtures for prompt quality, citation accuracy, and safe mutation.

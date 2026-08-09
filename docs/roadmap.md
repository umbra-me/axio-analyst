# Axio Analyst roadmap

The current architecture and security boundaries are documented in
[architecture.md](architecture.md). This document owns future product scope so
aspirational behavior is not confused with the implemented release.

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

## Phase 0 - read-only vertical slice

The user-facing analysis workflow landed in `0.7.0`; `0.8.0` retained that
read-only behavior while separating package boundaries, splitting the test
tree, adding manifest-aware migration, and exposing one validated version
through Binary Ninja.

Implemented through `0.8.0`:

- Explain or ask about the current function.
- Address-labelled HLIL with a configurable context cap.
- Provider-neutral Claude Code, Codex, and Ollama Cloud CLI adapters.
- Background execution, timeout, cancellation, safety flags, and no BNDB
  modification.
- Native Chat and Settings surfaces with session-local transcript, provider
  selection, streamed sanitized Markdown, progress, and elapsed time.
- Non-blocking Ollama catalog discovery with local registered-model fallback.
- Explicit `core/`, `application/`, `providers/`, `host/`, and `ui/` boundaries
  with stock-Python dependency contracts.
- Semantic-version visibility in plugin metadata, sidebar, Settings, About,
  and log surfaces.
- A nested-runtime installer that detects drift and can prune only known
  obsolete flat-layout modules.

### Current limitations

- Context includes one function's metadata and HLIL only; selections,
  callers/callees, strings, imports, and types are not gathered.
- Conversations are not restored after the sidebar is destroyed.
- Model suggestions do not guarantee account access.
- Usage, token, latency, and cost metadata is not stored or displayed.
- There is no structured evidence schema or proposed Binary Ninja transaction.
- Codex exposes completed agent messages rather than token-level deltas.
- CLI adapters cannot inspect arbitrary files or use unrestricted tools.

## Phase 1 - useful daily assistant

- Richer context preview before dispatch and persistent conversation storage.
- OpenAI-compatible and Anthropic API adapters.
- Environment/credential-store API keys and an OAuth token broker.
- Selection, callers/callees, imports, strings, and type context packs.
- Structured responses with citations, uncertainty, and usage metadata.

Before persistence is implemented, define a versioned location, schema,
migration policy, retention behavior, deletion/export behavior, and binary-hash
association. Credentials remain outside the workspace schema.

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

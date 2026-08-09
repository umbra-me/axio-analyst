# Axio Analyst architecture

Axio Analyst is a local, provider-neutral AI workspace for Binary Ninja. The
current release is a read-only investigation workflow with transparent context
packing, evidence navigation, optional bounded local history, provider
comparison, and usage accounting. Future product phases are tracked separately
in [the roadmap](roadmap.md).

## Dependency boundaries

```text
Binary Ninja entry point
  -> host registration and context
       -> Qt UI
       -> application use cases
            -> core contracts and policies
       -> provider adapter factory
            -> core provider contract
```

Dependencies point toward `core/`. The core and application layers do not
import Binary Ninja, Qt, subprocess, or network libraries. Provider adapters
implement the core provider contract. The host creates concrete adapters and
translates live Binary Ninja objects into serializable core models. The UI
coordinates widgets but does not supervise provider processes directly.

The repository root remains the importable Binary Ninja plugin directory.
`__init__.py` is deliberately only a host-aware loader so stock Python can
import the provider-neutral packages without a Binary Ninja installation.

## Implementation map

| Path | Responsibility |
| --- | --- |
| `core/models.py` | Serializable function/context bundles, provider configuration, usage, results, and errors. |
| `core/provider.py` | Provider interface and cancellation/stream callback types. |
| `core/prompts.py` | Exact context rendering and reverse-engineering prompt construction. |
| `core/policy.py` | Stable context ordering, deduplication, and deterministic total budgeting. |
| `core/evidence.py` | Address-citation extraction and validity classification. |
| `core/usage.py` | Provider-neutral usage and latency presentation. |
| `core/version.py` | Validate and expose the version from `plugin.json`. |
| `application/analyze.py` | Build a request, invoke an injected provider, and normalize timing/character usage. |
| `application/conversations.py` | Versioned bounded transcript schema, atomic JSON store, and Markdown export. |
| `providers/process.py` | Bounded subprocess supervision, pipe draining, timeout, and cancellation. |
| `providers/streaming.py` | Incremental JSONL decoding and terminal-sequence removal. |
| `providers/claude.py` | Claude Code command, parser, streaming, and result normalization. |
| `providers/codex.py` | Codex command, parser, streaming, and result normalization. |
| `providers/ollama.py` | Ollama command, cloud catalog, local-list parsing, and result normalization. |
| `providers/__init__.py` | Provider factory and stable adapter exports. |
| `host/context.py` | Gather the primary function and opt-in context packs into a bounded `ContextBundle`. |
| `host/model_discovery.py` | Coordinate remote and local Ollama discovery without blocking Qt. |
| `host/settings.py` | Register and access the machine-local `axioAnalyst.*` settings. |
| `host/storage.py` | Path-free sampled content fingerprint and Binary Ninja user-directory store location. |
| `host/task.py` | Context-preview and analysis `BackgroundTaskThread` lifecycles plus main-thread dispatch. |
| `host/registration.py` | Plugin commands and best-effort sidebar registration. |
| `ui/sidebar_view.py` | Compact chat/composer layout, dedicated context workspace, staged settings navigation, and direct UI signals. |
| `ui/sidebar.py` | Context, request/comparison, evidence navigation, persistence, export, and discovery coordination. |
| `ui/settings_page.py` | Staged provider, harness, and request-limit settings. |
| `ui/transcript.py` | Conversation state, completion-focused scrolling, sanitized Markdown, and internal evidence anchors. |
| `ui/progress.py` | Elapsed time and request-progress presentation. |
| `ui/markdown.py` | Raw-HTML escaping and scroll restoration. |

`tools/runtime_manifest.py` is the authoritative explicit allowlist used by
the development installer. A contract test ensures it covers every runtime
Python module under `application/`, `core/`, `host/`, `providers/`, and `ui/`.

## Current request sequence

```text
cursor/view notification
  -> ui/sidebar.py resolves the function containing the current offset
  -> user optionally selects context packs and builds an exact preview
  -> user chooses Explain or Ask and the UI captures selection/options
  -> host/settings.py provides RuntimeConfig
  -> host/task.py starts a cancellable BackgroundTaskThread
  -> host/context.py builds one frozen, bounded ContextBundle
  -> the exact snapshot is returned to the context preview
  -> application/analyze.py builds the prompt and invokes an injected provider
  -> providers/process.py supervises the selected authenticated CLI via stdin
  -> an optional comparison provider receives the same frozen prompt
  -> adapters normalize streaming, final text, and available usage metadata
  -> host/task.py coalesces callbacks through execute_on_main_thread
  -> ui/sidebar.py validates cited addresses and combines comparison results
  -> ui/transcript.py renders final text, internal evidence links, and usage
  -> an enabled local store atomically replaces the bounded transcript record
```

The sidebar stores only serializable conversation values. It does not retain
live Binary Ninja instructions or provider process objects after a request
completes. Moving the cursor updates the context card but does not change the
snapshot already dispatched. Persistence is off by default; when enabled, the
record is associated with a bounded sampled content fingerprint rather than a
source path.

## Threading and ownership

| Work | Owner | Thread/process boundary |
| --- | --- | --- |
| Cursor, controller, and widgets | `ui/` | Binary Ninja Qt main thread |
| HLIL rendering and task lifecycle | `host/context.py`, `host/task.py` | `BackgroundTaskThread` |
| Local JSON replacement/export | `application/conversations.py`, `ui/sidebar.py` | Qt main thread after bounded serialization/user action |
| Provider inference | `providers/` | Supervised child process |
| Child stdout/stderr reads | `providers/process.py` | Two daemon reader threads per request |
| Stream/progress UI dispatch | `host/task.py` | Coalesced, then `execute_on_main_thread` |
| Ollama public catalog fetch | `providers/ollama.py`, `host/model_discovery.py` | Dedicated daemon thread |
| Ollama local fallback discovery | `host/model_discovery.py` | Asynchronous Qt `QProcess` |

No Qt widget may be updated directly from a provider, reader, catalog, or
Binary Ninja background thread. Callback dispatch tolerates a sidebar being
destroyed while a request finishes.

## Failure containment

- Function commands are registered before importing the sidebar so a Qt UI
  registration failure does not remove one-shot analysis commands.
- Expected provider failures use `ProviderError`; cancellation has its own
  `ProviderCancelled` path and is not presented as an unexpected crash.
- The shared process runner limits combined stdout/stderr to 8 MB and bounds
  displayed nonzero-exit diagnostics to 2,000 characters.
- Sidebar destruction stops elapsed-time tracking and cancels an active task.
  Late callbacks check widget liveness.
- Raw provider HTML is escaped before Qt's Markdown renderer sees it. Generic
  links are not opened. Only `axio://address/<hex>` anchors created by the UI
  after BinaryView validation can trigger navigation.
- Conversation filenames are validated SHA-256 hex identifiers, records are
  capped at 200 messages and 8 MB, and saves use an atomic same-directory
  replacement with restrictive permissions where the OS supports them.
- Comparison failures are contained per provider so one successful result can
  still be inspected; single-provider failures retain the normal error path.

## Provider and authentication boundary

Claude Code, Codex, and Ollama Cloud are supervised local CLI adapters behind
one provider interface. Each adapter declares its command and output protocol,
while `providers/process.py` owns the shared execution safety behavior.

The adapters delegate authentication to their installed CLI. They do not open
credential files. Prompts are written over stdin, temporary work occurs in a
dedicated directory, and provider tools or persistence are disabled where the
CLI exposes those controls.

Future native HTTP adapters must keep API keys in environment variables or an
OS credential store, never in tracked files, Binary Ninja settings, BNDBs, or
conversation data. OAuth refresh tokens require a dedicated credential broker.

## Data and mutation boundary

The binary base filename, primary function metadata, and bounded
address-labelled primary HLIL are sent after an explicit Ask or Explain action.
Selection, direct callers/callees, referenced strings/imports, and relevant
types are sent only when their visible checkbox is enabled. Source paths, whole
binaries, BNDB files, indirect neighbourhoods, and arbitrary unrelated
functions are not sent.

The optional schema-version-1 conversation record contains the binary display
name, timestamp, role/body/meta text, and validated/unresolved evidence
addresses. It does not contain a source path, context snapshot, prompt, provider
credential, or raw binary bytes. Persistence is off by default. **Clear**
deletes the exact fingerprint record and **Export** writes a user-selected
Markdown file. The current release never changes names, types, comments,
analysis, or BNDB state.

Future writes must be represented as proposed operations, validated against
current analysis state, shown as a reviewable diff, and applied as one undoable
transaction with an audit record.

## Constraints

- Do not copy proprietary Sidekick implementation, prompts, or branding.
- Do not silently send a whole binary or source path to a provider.
- Do not treat model output as verified analysis.
- Do not let providers write directly to Binary Ninja.
- Do not store OAuth tokens or API keys in the repository, BNDB, workspace, or
  request log.
- Keep non-UI commands usable when sidebar registration fails.
- Depend only on PySide6 modules shipped with Binary Ninja unless a separate
  distribution decision explicitly approves another runtime dependency.

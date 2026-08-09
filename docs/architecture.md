# Axio Analyst architecture

Axio Analyst is a local, provider-neutral AI workspace for Binary Ninja. The
current release is a read-only current-function analysis workflow. Future
product phases are tracked separately in [the roadmap](roadmap.md).

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
| `core/models.py` | Serializable function context, provider configuration, results, and errors. |
| `core/provider.py` | Provider interface and cancellation/stream callback types. |
| `core/prompts.py` | Bounded reverse-engineering prompt construction. |
| `core/policy.py` | Deterministic context truncation policy. |
| `core/version.py` | Validate and expose the version from `plugin.json`. |
| `application/analyze.py` | Build a request and invoke an injected provider. |
| `providers/process.py` | Bounded subprocess supervision, pipe draining, timeout, and cancellation. |
| `providers/streaming.py` | Incremental JSONL decoding and terminal-sequence removal. |
| `providers/claude.py` | Claude Code command, parser, streaming, and result normalization. |
| `providers/codex.py` | Codex command, parser, streaming, and result normalization. |
| `providers/ollama.py` | Ollama command, cloud catalog, local-list parsing, and result normalization. |
| `providers/__init__.py` | Provider factory and stable adapter exports. |
| `host/context.py` | Convert Binary Ninja function HLIL into `FunctionContext`. |
| `host/model_discovery.py` | Coordinate remote and local Ollama discovery without blocking Qt. |
| `host/settings.py` | Register and access the machine-local `axioAnalyst.*` settings. |
| `host/task.py` | `BackgroundTaskThread` lifecycle and main-thread callback dispatch. |
| `host/registration.py` | Plugin commands and best-effort sidebar registration. |
| `ui/sidebar_view.py` | Sidebar widget construction and direct UI signals. |
| `ui/sidebar.py` | Current-function, request, and model-discovery coordination. |
| `ui/settings_page.py` | Staged provider, harness, and request-limit settings. |
| `ui/transcript.py` | Session-local conversation state and Markdown rendering. |
| `ui/progress.py` | Elapsed time and request-progress presentation. |
| `ui/markdown.py` | Raw-HTML escaping and scroll restoration. |

`tools/runtime_manifest.py` is the authoritative explicit allowlist used by
the development installer. A contract test ensures it covers every runtime
Python module under `application/`, `core/`, `host/`, `providers/`, and `ui/`.

## Current request sequence

```text
cursor/view notification
  -> ui/sidebar.py resolves the function containing the current offset
  -> user chooses Explain or Ask
  -> host/settings.py provides RuntimeConfig
  -> host/task.py starts a cancellable BackgroundTaskThread
  -> host/context.py renders address-labelled HLIL and applies the core limit
  -> application/analyze.py builds the prompt and invokes an injected provider
  -> providers/process.py supervises the selected authenticated CLI via stdin
  -> the adapter normalizes streaming events and the final ProviderResult
  -> host/task.py coalesces callbacks through execute_on_main_thread
  -> ui/transcript.py replaces the active streamed message with the final text
```

The sidebar stores only serializable conversation values for its own lifetime.
It does not retain live Binary Ninja instructions or provider process objects
after a request completes. Moving the cursor updates the context card but does
not rewrite the context recorded on earlier messages.

## Threading and ownership

| Work | Owner | Thread/process boundary |
| --- | --- | --- |
| Cursor, controller, and widgets | `ui/` | Binary Ninja Qt main thread |
| HLIL rendering and task lifecycle | `host/context.py`, `host/task.py` | `BackgroundTaskThread` |
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
- Raw provider HTML is escaped before Qt's Markdown renderer sees it; links are
  not opened from the transcript.

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

Only the binary base filename, function metadata, and bounded current-function
HLIL are sent after an explicit Ask or Explain action. Source paths, whole
binaries, BNDB files, and unrelated functions are not sent.

No durable conversation schema exists in `0.8.0`. Provider credentials must
remain separate from any future workspace store. The current release never
changes names, types, comments, analysis, or BNDB state.

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

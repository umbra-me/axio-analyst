# Axio Analyst design

Axio Analyst is a local, provider-neutral AI workspace for Binary Ninja. It is
inspired by the category of workflows offered by Binary Ninja Sidekick, but it
is an independent plugin with its own implementation and data model.

## Product end state

The finished plugin should support six connected workflows:

1. **Ask and investigate** - chat about a selection, function, subsystem, or
   whole binary; let bounded agents gather more context through explicit tools.
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
   workflows with per-tool read/write permissions, budgets, cancellation, and
   a transaction log.

The UI eventually becomes a dockable workspace with chat, context preview,
findings, proposed changes, provider status, token/cost accounting, and a
request trace. Menu commands remain available for fast one-shot actions.

## Architecture

```text
Binary Ninja UI
  -> context builder (selection/function/binary)
  -> request policy (consent, redaction, size and cost limits)
  -> task/agent orchestrator
       -> HTTP provider adapter
       -> local model adapter
       -> headless harness adapter
  -> normalized response and evidence model
  -> report / notebook / proposed BNDB transaction
```

The provider boundary accepts a normalized request and returns text, structured
artifacts, usage, and provider metadata. It must not know about Binary Ninja
objects. The Binary Ninja layer converts live objects into serializable context
and is the only layer allowed to mutate a database.

### Current implementation map

| File | Responsibility |
| --- | --- |
| `models.py` | Provider-neutral context, configuration, result, and error types. |
| `prompts.py` | Bounded reverse-engineering prompt and truncation policy. |
| `providers.py` | Supervised Claude Code, Codex, and Ollama Cloud child processes plus output parsing. |
| `settings.py` | Binary Ninja setting registration and machine-local provider selection. |
| `task.py` | HLIL rendering, background execution, cancellation, and main-thread callbacks. |
| `sidebar.py` | Native Chat surface, Markdown transcript, streaming state, and progress UI. |
| `settings_page.py` | Native provider, harness, and request-limit settings surface. |
| `rendering.py` | Raw-HTML escaping for untrusted Markdown content. |
| `registration.py` | Function commands, sidebar command, and isolated UI registration. |

### Current request sequence

```text
cursor/view notification
  -> sidebar resolves the first function containing the current offset
  -> user chooses Explain or Ask
  -> persisted settings are read into RuntimeConfig
  -> AnalyzeFunctionTask starts as a cancellable BackgroundTaskThread
  -> function HLIL is rendered as "address: instruction" lines
  -> deterministic character truncation is applied
  -> provider-neutral prompt is written to a supervised CLI over stdin
  -> stdout/stderr reader threads prevent pipe deadlock
  -> parser emits normalized stream text and a final ProviderResult
  -> coalesced callbacks return through execute_on_main_thread
  -> sidebar replaces the active streamed message with the final result
```

The sidebar stores only `ChatMessage` values for its own lifetime. It does not
hold live Binary Ninja instructions or provider process objects after a request
completes. Moving the cursor updates the context card but does not rewrite past
messages; each user and assistant message records its function/provider context
at dispatch or completion.

### Threading and ownership

| Work | Owner | Thread/process boundary |
| --- | --- | --- |
| Cursor and widget state | `sidebar.py` | Binary Ninja Qt main thread |
| HLIL rendering and request lifecycle | `task.py` | `BackgroundTaskThread` |
| Provider inference | `providers.py` | Supervised child process |
| Child stdout/stderr reads | `providers.py` | Two daemon reader threads per request |
| Stream/progress UI update | `task.py` | Coalesced, then `execute_on_main_thread` |
| Ollama public catalog fetch | `sidebar.py` and `providers.py` | Dedicated daemon thread |
| Ollama local fallback discovery | `sidebar.py` | Asynchronous Qt `QProcess` |

No Qt widget may be updated directly from a provider, reader, catalog, or
Binary Ninja background thread. Callback dispatch tolerates a sidebar being
destroyed while a request is finishing.

### Failure containment

- Function commands are registered before importing the sidebar so a Qt UI
  registration failure does not remove one-shot analysis commands.
- Expected provider failures use `ProviderError`; cancellation has its own
  `ProviderCancelled` path and does not appear as an unexpected crash.
- The shared process runner limits combined stdout/stderr to 8 MB and bounds
  displayed nonzero-exit diagnostics to 2,000 characters.
- A sidebar destruction event stops its elapsed timer and cancels an active
  task. Late callbacks check widget liveness.
- Raw provider HTML is escaped before Qt's Markdown renderer sees it; links are
  not opened from the transcript.

### Backend families

- **Native APIs:** Anthropic Messages, OpenAI Responses, Google, and compatible
  endpoints such as Ollama or vLLM.
- **Headless harnesses:** Claude Code (`claude -p`), Codex (`codex exec`), and
  Ollama Cloud (`ollama run`), with room for other CLIs. A harness owns its
  authentication and Axio Analyst talks to it through stdin/stdout using
  structured output where available.
- **Local inference:** OpenAI-compatible local servers and, later, direct local
  runtimes if they justify the dependency cost.

Model selection is separate from backend selection. Named roles such as
`fast`, `deep`, and `embedding` map to a backend/model pair so workflows do not
hardcode vendors.

## Authentication and secrets

Each adapter declares an authentication strategy:

- API keys come from environment variables or an OS credential store, never a
  tracked file or BNDB.
- OAuth uses Authorization Code with PKCE when supported, or device
  authorization for terminal-first providers. Refresh tokens belong in the OS
  credential store; access tokens stay in memory and are redacted from logs.
- Harness adapters delegate auth to the installed CLI. The current Claude Code,
  Codex, and Ollama Cloud adapters never open their credential files.
- Local endpoints may explicitly declare that no authentication is required,
  but non-loopback unauthenticated endpoints should be rejected by default.

Provider capability discovery should report chat, tool use, structured output,
vision, embeddings, context size, and auth state without exposing credentials.

## Agent and tool model

Long-running investigations need a controlled tool loop rather than dumping an
entire binary into one prompt. Initial read tools should cover function/IL
rendering, callers/callees, references, strings, imports, types, symbols, and
bounded byte reads. Write tools arrive later and return proposed operations;
the plugin validates and previews them before applying one Binary Ninja undo
transaction.

Headless coding harnesses must not receive filesystem or shell access merely
because they support it. The default profile is analysis-only. Future tool use
should go through an explicit Axio Analyst MCP server or broker with a narrow
allowlist, per-request permission decisions, timeouts, and cancellation.

## Local data

Workspace data should be local-first and separate from provider credentials.
The durable schema needs IDs for sessions, messages, artifacts, findings,
evidence references, proposed/applied transactions, provider requests, and
index versions. Store hashes of the binary and relevant analysis state so stale
claims can be marked for re-verification. Export must be explicit because notes
can contain proprietary code and provider output.

No durable workspace schema exists in `0.7.0`. When persistence is introduced,
it should be versioned independently from Binary Ninja settings and use an
explicit location and migration policy. Provider credentials must remain
outside that schema. Conversation deletion, export, retention, and binary-hash
association need product behavior before storage code is added.

## Delivery phases

### Phase 0 - vertical slice (implemented)

- Explain or ask about the current function.
- Address-labelled HLIL with a configurable context cap.
- Provider-neutral Python interface with Claude Code, Codex, and Ollama Cloud
  adapters.
- Background execution, timeout, cancellation, safe CLI flags, and no BNDB
  modification.
- Native right sidebar with separate Chat and Settings views, cursor-following
  function context, session-local transcript, provider/model/reasoning controls,
  harness paths, request limits, and cancellation.
- Sanitized Markdown responses, provider-supported incremental output, honest
  phase progress, and elapsed time.
- Settings use one staged Apply/Revert boundary across provider defaults,
  executable paths, and request limits.
- A Binary Ninja background task plus dedicated stdout and stderr reader threads
  keep provider work and pipe draining off the GUI thread. Stream updates are
  coalesced before returning to the main thread.
- Streaming follows the live tail only while the reader remains near the
  bottom; manually scrolling upward preserves the reading position.
- Non-blocking discovery from Ollama's public cloud catalog, with registered
  local cloud models as an offline fallback.
- Catalog discovery sends only a public HTTP GET and never includes provider
  credentials, function context, or binary metadata.

### Current limitations

- Context is one function's typed metadata and address-labelled HLIL; callees,
  callers, selections, strings, imports, and types are not gathered yet.
- Conversations live only in the current sidebar instance and are not restored.
- Model suggestions are conveniences, not an account-access guarantee. Claude,
  Codex, and Ollama validate selections when a request is sent.
- No usage, token, latency, or cost metadata is stored or displayed.
- Markdown is presentation only. There is no structured evidence schema or
  proposed Binary Ninja transaction yet.
- Streaming granularity follows the harness: Claude supplies partial-message
  deltas, Ollama supplies pipe chunks, and Codex JSONL exposes its completed
  agent message rather than token deltas.
- The CLI adapters are intentionally tool-less or read-only and cannot inspect
  arbitrary files on behalf of the model.

### Phase 1 - useful daily assistant

- Richer context preview before dispatch and persistent conversation storage.
- OpenAI-compatible and Anthropic API adapters.
- Environment/credential-store API keys and an OAuth token broker.
- Selection, callers/callees, imports, strings, and type context packs.
- Structured response schema with citations, uncertainties, and usage.

### Phase 2 - reversible transformations

- Rename, retype, comment, and structure suggestions as a reviewable diff.
- Validate addresses and object identities against current analysis state.
- Apply accepted changes in one undo action and record the transaction.
- Persistent notebook, findings, and rejected hypotheses.

### Phase 3 - agentic investigation

- Read-only Binary Ninja tool broker and MCP surface.
- Bounded multi-step investigations with turn, time, context, and cost budgets.
- Semantic indexes and evidence-aware search.
- Repeatable skills/workflows with inspectable traces.

### Phase 4 - workspace intelligence

- Cross-binary projects, code/data-flow maps, debugger evidence, and stale
  finding invalidation.
- Import/export and collaboration without coupling analysis data to a provider.
- Evaluation fixtures for prompt quality, citation accuracy, and safe mutation.

## Non-goals and constraints

- Do not copy Sidekick's proprietary implementation, prompts, or branding.
- Do not silently send a whole binary or source path to a provider.
- Do not treat model output as verified analysis.
- Do not let providers write directly to Binary Ninja.
- Do not store OAuth tokens or API keys in the repository, BNDB, notebook, or
  request log.
- Keep non-UI commands usable when sidebar registration fails, and depend only
  on PySide6 modules shipped with Binary Ninja.

# Provider contracts

All current backends are supervised local child processes. The provider layer
accepts a normalized prompt and returns a normalized result without importing
Binary Ninja. Authentication, network transport, account entitlements, and
provider-side retention remain the responsibility of the installed CLI.

`core/provider.py` defines the interface, `application/analyze.py` owns the
provider-neutral use case, and `providers/__init__.py` selects the concrete
Claude Code, Codex, or Ollama adapter from `ProviderConfig`. Individual command
and parser implementations live in `providers/claude.py`, `codex.py`, and
`ollama.py`; shared supervision and stream decoding live in `process.py` and
`streaming.py`; OS process-tree cleanup lives in `process_tree.py`.

## Shared process contract

For every request Axio Analyst:

1. creates a unique `axio-analyst-*` working directory under the OS temp
   directory and removes it after cleanup;
2. launches the configured executable without a visible console window on
   Windows;
3. submits the prompt on a separate daemon writer so a blocked stdin pipe
   does not prevent timeout or cancellation checks;
4. drains stdout and stderr concurrently on daemon reader threads through a
   queue capped at 64 chunks of up to 4,096 bytes;
5. incrementally decodes UTF-8 with replacement for malformed bytes;
6. enforces cancellation, the configured timeout, and an 8 MB combined output
   limit, counted by the readers before queueing;
7. reports a bounded stderr diagnostic when the process exits unsuccessfully;
8. parses the provider output into a `ProviderResult`;
9. normalizes elapsed seconds and input/output character counts, retaining
   token, cache, and cost fields when structured output supplies them.

Prompts are never command-line arguments. Provider work does not run on the Qt
GUI thread. Stream updates are coalesced before being returned to the main
thread. While receiving, the transcript inserts sanitized literal text into
the active response up to a 64,000-character live-preview ceiling, with a
visible notice when reached. Raw chunks are retained separately and assembled
for snapshots or terminal rendering, avoiding repeated growing-string copies.
The full result or cancelled/failed partial text is parsed as Markdown once at
the terminal update. Existing conversation Markdown is not reparsed for every
incoming chunk.

The deadline starts before process creation and remains checked during stdin
submission, streaming, and post-EOF process waiting. Python cannot preempt a
blocked OS process-creation call. Cleanup runs on success and every failure,
including callback exceptions, with kill/wait escalation attempted even if
graceful cleanup raises: POSIX children use a new session/process group;
Windows children are assigned to a kill-on-close Job Object. Windows attachment
occurs after launch, so descendants created before attachment are not proven
contained. The Windows path still requires live validation. POSIX descendants
that deliberately escape the process group are also outside this cleanup
mechanism; it is lifecycle supervision, not a security sandbox. Cleanup waits
up to two seconds before escalation and another two seconds after killing.

## Claude Code

Command shape:

```text
claude -p
  --output-format stream-json
  --include-partial-messages
  --verbose
  --safe-mode
  --disable-slash-commands
  --no-session-persistence
  --permission-mode dontAsk
  --no-chrome
  --tools ""
  [--model MODEL]
  [--effort EFFORT]
```

The prompt arrives on stdin. Axio Analyst accepts a single JSON document, a
JSON event array, or JSON Lines output. Partial content-block deltas update the
transcript while the request runs. The final result is taken from the result
event; a model reported by Claude takes precedence over the configured alias.
Result-level `usage`, `total_cost_usd`, and `duration_ms` values populate token,
cached-token, cost, and duration metadata when present.

The empty tools list and safe flags are intentional. The harness receives the
provided HLIL text but cannot inspect the local filesystem or invoke Binary
Ninja tools on behalf of the model.

## Codex

Command shape:

```text
codex exec
  --json
  --color never
  --sandbox read-only
  --ephemeral
  --ignore-user-config
  --ignore-rules
  --disable shell_tool
  --disable view_image
  --config web_search="disabled"
  --skip-git-repo-check
  [--model MODEL]
  [--config model_reasoning_effort="EFFORT"]
  -
```

The trailing `-` selects stdin. Ephemeral execution prevents session reuse, the
read-only sandbox requests write restrictions, and user configuration/rules
are ignored. Shell and image tools and web search are explicitly disabled.
These controls do **not** establish snapshot-only filesystem or tool access.
In the inspected Codex `0.153.2` [tool registration source](https://github.com/openai/codex/blob/rust-v0.153.2/codex-rs/core/src/tools/spec_plan.rs),
patch-tool registration is independent of shell/image switches. No supported
global tool-off control was established. Do not rely on this adapter to keep
unrelated readable files confidential; that release gate remains open.

Axio Analyst parses JSON Lines and accepts a final agent message only with a
`turn.completed` event and no `error` or `turn.failed` event. A failed turn
remains a failure even if it emitted useful-looking text first. A
`turn.completed.usage` object populates input,
cached-input, and output token counts when present. Current Codex JSONL does
not expose token-level text deltas through this adapter.

## Ollama Cloud

Command shape:

```text
ollama run MODEL --nowordwrap --hidethinking [--think=EFFORT]
```

The model is required. Axio Analyst sets `OLLAMA_NOHISTORY=1` only for the child
process, strips ANSI terminal sequences, and streams cleaned stdout chunks.
`--hidethinking` keeps hidden reasoning out of the conversation surface.
The text-mode CLI does not currently provide normalized token or cost fields,
so Axio Analyst displays measured duration and input/output character counts.

Cloud model discovery is independent of request execution. It first uses the
public Ollama catalog and falls back to `ollama list`; see
[Configuration reference](configuration.md#ollama-cloud-discovery).

## Prompt contract

The normalized prompt instructs the model to:

- answer only from supplied context;
- separate observed facts from inference;
- cite important claims using HLIL addresses such as `0x140001000`;
- state when context is insufficient;
- avoid inventing symbols, types, or behavior;
- avoid proposing edits or renames unless the question asks for them.

The payload contains the binary base name, architecture, platform, primary
function name/start/type, item count, total characters, truncation state, exact
context snapshot, and user question. The snapshot always includes bounded
address-labelled primary-function HLIL. It includes selection, direct
callers/callees, referenced strings/imports, or relevant types only when the
corresponding UI option was captured at dispatch. The binary's full source path
is omitted.

## Provider comparison

The header overflow menu, under **Compare with**, selects one other configured
backend to run beside the active provider. Comparison is off by default and
costs no resting layout space. Axio Analyst builds the `ContextBundle` once,
then invokes the primary
and comparison adapters sequentially with the exact same normalized prompt.
Primary-provider streaming remains visible; the completed transcript replaces
it with labelled provider sections and separate usage summaries. A comparison
provider failure is contained and shown beside any successful result. Choosing
the same backend as the active provider collapses to a normal single request.
Cancelling the comparison preserves a completed primary result and its
findings/usage, while marking the comparison cancelled. Cancelling the primary
retains the normal partial-text cancellation path.

Comparison is deliberately not concurrent: this avoids competing child
processes, keeps cancellation deterministic, and makes local resource usage
predictable. It is a qualitative inspection tool, not a statistically
controlled benchmark or a claim that provider output formats are equivalent.

## Errors and cancellation

Expected failures become user-visible `ProviderError` messages:

- executable path is empty or not found;
- provider process cannot start;
- configured timeout expires;
- combined stdout/stderr exceeds 8 MB;
- process exits nonzero;
- structured output is malformed or contains no final response;
- Ollama model is empty or produces no text.

Cancellation uses `ProviderCancelled`, distinct from a provider error, and
always enters process-tree cleanup. Partial streamed text remains visible and
is marked cancelled or failed in the transcript.

## Adding another provider

A new adapter should implement `Provider.complete`, return `ProviderResult`,
be exported through the provider factory, and remain importable under stock
Python. It must define:

- executable/endpoint and authentication ownership;
- exact command or HTTP request contract;
- stdin and command-line handling;
- structured output and streaming parser;
- timeout, cancellation, and output limits;
- credential and retention behavior;
- model and effort capabilities;
- unit tests for success, malformed output, failure, timeout, cancellation, and
  streaming boundaries.

Add the module to `tools/runtime_manifest.py`. The distribution contract test
must still prove that providers do not import Binary Ninja or Qt and that every
runtime Python file is included in development installs.

Direct HTTP providers are roadmap work. They will require a separate credential
broker and must not place secrets in Binary Ninja settings or BNDB state.

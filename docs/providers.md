# Provider contracts

All current backends are supervised local child processes. The provider layer
accepts a normalized prompt and returns a normalized result without importing
Binary Ninja. Authentication, network transport, account entitlements, and
provider-side retention remain the responsibility of the installed CLI.

## Shared process contract

For every request Axio Analyst:

1. creates or reuses a dedicated temporary working directory named
   `axio-analyst` under the operating-system temp directory;
2. launches the configured executable without a visible console window on
   Windows;
3. sends the complete prompt over stdin;
4. drains stdout and stderr concurrently on daemon reader threads;
5. incrementally decodes UTF-8 with replacement for malformed bytes;
6. enforces cancellation, the configured timeout, and an 8 MB combined output
   limit;
7. reports a bounded stderr diagnostic when the process exits unsuccessfully;
8. parses the provider output into a `ProviderResult`.

Prompts are never command-line arguments. Provider work does not run on the Qt
GUI thread. Stream updates are coalesced before being returned to the main
thread to avoid excessive UI redraws.

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
  --skip-git-repo-check
  [--model MODEL]
  [--config model_reasoning_effort="EFFORT"]
  -
```

The trailing `-` selects stdin. Ephemeral execution prevents session reuse, the
read-only sandbox prevents writes, and user configuration/rules are ignored so
they cannot silently broaden the analysis task. Axio Analyst parses JSON Lines
events, surfaces lifecycle status where available, and uses the completed
agent message as the response. Current Codex JSONL does not expose token-level
text deltas through this adapter.

## Ollama Cloud

Command shape:

```text
ollama run MODEL --nowordwrap --hidethinking [--think=EFFORT]
```

The model is required. Axio Analyst sets `OLLAMA_NOHISTORY=1` only for the child
process, strips ANSI terminal sequences, and streams cleaned stdout chunks.
`--hidethinking` keeps hidden reasoning out of the conversation surface.

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

The payload contains the binary base name, architecture, platform, function
name/start/type, truncation state, address-labelled HLIL, and user question.
The binary's full source path is omitted.

## Errors and cancellation

Expected failures become user-visible `ProviderError` messages:

- executable path is empty or not found;
- provider process cannot start;
- configured timeout expires;
- user cancels the task;
- combined stdout/stderr exceeds 8 MB;
- process exits nonzero;
- structured output is malformed or contains no final response;
- Ollama model is empty or produces no text.

Cancellation first terminates the process, waits up to two seconds, then kills
it if necessary. Partial streamed text remains visible and is marked cancelled
or failed in the transcript.

## Adding another provider

A new adapter should implement `Provider.complete`, return `ProviderResult`,
and remain importable under stock Python. It must define:

- executable/endpoint and authentication ownership;
- exact command or HTTP request contract;
- stdin and command-line handling;
- structured output and streaming parser;
- timeout, cancellation, and output limits;
- credential and retention behavior;
- model and effort capabilities;
- unit tests for success, malformed output, failure, timeout, cancellation, and
  streaming boundaries.

Direct HTTP providers are roadmap work. They will require a separate credential
broker and must not place secrets in Binary Ninja settings or BNDB state.

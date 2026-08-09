# Configuration reference

Axio Analyst registers machine-local Binary Ninja user settings under the
`axioAnalyst` group. Project and resource scopes are ignored deliberately so a
BNDB cannot carry provider selection or executable paths to another machine.

The Settings page stages edits until **Apply settings** is chosen. **Revert**
reloads the last persisted values. Provider-specific model and effort choices
are retained independently when switching between providers.

## Settings

| Key | Type | Default | Allowed values or range | Purpose |
| --- | --- | --- | --- | --- |
| `axioAnalyst.backend` | string | `claude-code` | `claude-code`, `codex-cli`, `ollama-cloud` | Active provider adapter. |
| `axioAnalyst.claudeCode.executable` | string | `claude` | Executable name or absolute path | Claude Code CLI to launch. |
| `axioAnalyst.claudeCode.model` | string | empty | Editable; suggestions include `opus`, `sonnet`, `fable` | Empty delegates model selection to Claude Code. |
| `axioAnalyst.claudeCode.reasoningEffort` | string | empty | `low`, `medium`, `high`, `xhigh`, `max` | Empty uses the CLI/model default. |
| `axioAnalyst.codex.executable` | string | `codex` | Executable name or absolute path | Codex CLI to launch. |
| `axioAnalyst.codex.model` | string | empty | Editable model identifier | Empty delegates model selection to Codex. |
| `axioAnalyst.codex.reasoningEffort` | string | empty | `low`, `medium`, `high`, `xhigh`, `max`, `ultra` | Passed as the Codex model reasoning effort override. |
| `axioAnalyst.ollamaCloud.executable` | string | `ollama` | Executable name or absolute path | Ollama CLI to launch and use for fallback discovery. |
| `axioAnalyst.ollamaCloud.model` | string | `gpt-oss:120b-cloud` | Editable cloud tag | Required for Ollama requests. |
| `axioAnalyst.ollamaCloud.reasoningEffort` | string | empty | `low`, `medium`, `high` | Passed through the Ollama `--think` option. |
| `axioAnalyst.timeoutSeconds` | integer | `300` | `10` to `3600` | Wall-clock limit for one provider process. |
| `axioAnalyst.maxContextChars` | integer | `60000` | `1000` to `500000` | Maximum rendered HLIL characters included in one prompt. |

Model lists are suggestions, not guarantees of access. The selected provider
validates the model when the request runs. An arbitrary full model identifier
can be typed into the editable model field.

## Request-time behavior

The persisted settings are read when a request starts. Unsaved edits on the
Settings page do not affect a request until **Apply settings** is chosen.

The context limit applies after each HLIL instruction is rendered with its
address. Truncated context ends with:

```text
[HLIL truncated by Axio Analyst]
```

The prompt also tells the provider whether truncation occurred. Increasing the
limit can improve coverage but sends more binary-derived text and may increase
latency or provider usage.

The timeout covers process startup, stdin submission, streaming, and process
completion. Cancellation terminates the child process, waits briefly, and
kills it only if graceful termination does not complete.

## Ollama Cloud discovery

Selecting Ollama Cloud or choosing **Refresh** starts asynchronous discovery:

1. Fetch `https://ollama.com/api/tags` with a 10-second timeout and 1 MB
   response limit.
2. Convert catalog entries to runnable `:cloud` or `-cloud` tags.
3. If the public request fails or contains no usable entries, run
   `<ollama executable> list` and keep only registered cloud tags.
4. If both methods fail, preserve the editable field so a model can be entered
   manually.

The public catalog request sends no credentials, function context, binary
metadata, or configured model. Discovery runs separately from analysis and
does not block the Binary Ninja GUI thread.

## Storage and secret handling

Binary Ninja stores user settings in its user directory. The plugin stores no
API keys, OAuth tokens, provider cookies, conversation transcript, prompt
history, or binary contents. Executable paths and selected model names may be
sensitive on shared machines, so do not commit a populated Binary Ninja
`settings.json` to this repository.

The sidebar transcript is in memory only and is cleared when the widget is
destroyed or when **Clear** is chosen. Provider CLIs may have their own logging,
telemetry, retention, and server-side policies; consult the selected provider
before sending proprietary material.

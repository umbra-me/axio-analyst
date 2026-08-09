# Configuration reference

Axio Analyst registers machine-local Binary Ninja user settings under the
`axioAnalyst` group. Project and resource scopes are ignored deliberately so a
BNDB cannot carry provider selection or executable paths to another machine.

The Settings page stages edits until **Apply settings** is chosen. **Revert**
reloads the last persisted values. Provider-specific model and effort choices
are retained independently when switching between providers.

The plugin version is not a user setting. `plugin.json` owns the semantic
version, and `core/version.py` validates it during import. Binary Ninja exposes
that value in plugin metadata while Axio Analyst displays it in the sidebar,
Settings page, About command, and registration log.

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
| `axioAnalyst.maxContextChars` | integer | `60000` | `1000` to `500000` | Maximum combined characters across every enabled context item. |
| `axioAnalyst.persistConversations` | boolean | `false` | `true`, `false` | Restore and update a bounded transcript for the current binary. |

Model lists are suggestions, not guarantees of access. The selected provider
validates the model when the request runs. An arbitrary full model identifier
can be typed into the editable model field.

## Request-time behavior

The persisted settings are read when a request starts. Unsaved edits on the
Settings page do not affect a request until **Apply settings** is chosen.

The context limit applies to the combined item text after each HLIL instruction
is rendered with its address. The primary function is the only default item.
Selection, direct callers/callees, strings, imports, and types are selected in
the dedicated **Context** workspace for each request; those choices are not
hidden settings. The workspace replaces the chat content while it is open, so
its exact preview cannot collapse the transcript. With any extra pack enabled,
the primary function normally receives up to 60 percent of
the combined budget (with a 1,000-character floor), and each neighbour receives
at most 8,000 characters so later items have a chance to fit. The deterministic
policy preserves item order, deduplicates exact repeats, and labels every
truncation.

Current-function truncation ends with:

```text
[HLIL truncated by Axio Analyst]
```

Other items use the same marker with their visible label. The prompt tells the
provider the item count, total characters, and bundle truncation state.
**Build preview** displays item labels, kinds, addresses, exact text, sizes, and
truncation before dispatch. Every Ask/Explain action rebuilds and freezes a new
snapshot from the captured selection and options. Increasing the limit or
enabling packs sends more binary-derived text and may increase latency or usage.

The compact composer keeps comparison off by default. Choose **Compare** to
reveal the second-provider selector. While an analysis request is active,
**Stop request** occupies the submit position; it is not shown as a permanently
disabled third action.

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
API keys, OAuth tokens, provider cookies, full prompts, context snapshots, or
binary bytes. Executable paths and selected model names may be sensitive on
shared machines, so do not commit a populated Binary Ninja `settings.json`.

Conversation persistence is off by default. When enabled, schema-version-1
records are stored below:

```text
<Binary Ninja user directory>/axio-analyst/conversations/<fingerprint>.json
```

The 64-character filename is derived from bounded samples of the BinaryView
contents and address span; no source path is embedded in it. A record contains
the binary base name, updated timestamp, up to 200 role/body/meta messages, and
validated/unresolved evidence addresses. Each message is limited to 1 MB and a
record to 8 MB. Saves use same-directory atomic replacement and request owner-
only permissions where supported. **Clear** deletes only the exact current
fingerprint record. Disabling persistence stops future load/save but deliberately
does not silently delete an existing record; use **Clear** for deletion.

**Export** is available regardless of persistence. It writes the visible
conversation as Markdown only after the user chooses a destination. Provider
CLIs may have their own logging, telemetry, retention, and server-side policies;
consult the selected provider before sending proprietary material.

No `axioAnalyst.*` key stores the plugin version. Upgrading the plugin changes
runtime files and metadata without rewriting the user's provider selection,
executable paths, request limits, persistence preference, or credentials.

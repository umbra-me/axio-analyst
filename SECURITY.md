# Security policy

## Supported version

Axio Analyst is pre-release. Only the latest development version on `main` is
currently supported. The current source version is `0.9.0`. A versioned
support table will be added when tagged releases begin.

## Reporting a vulnerability

Until a dedicated private reporting address or GitHub private-vulnerability
workflow is published, contact the repository owner through an established
private channel. Do not open a public issue containing:

- proprietary binaries, source, decompilation, or BNDB content;
- provider prompts or unsanitized responses;
- API keys, OAuth tokens, cookies, credential files, or account identifiers;
- personal data, internal paths, or customer information.

Include only the minimum sanitized reproduction: affected version/commit,
Binary Ninja and operating-system versions, provider CLI/version if relevant,
impact, reproduction steps, and a non-proprietary fixture where possible. The
`samples/demo` binary is preferred for public reproductions.

## Current trust boundaries

Axio Analyst treats Binary Ninja analysis context and provider responses as
sensitive, untrusted data crossing distinct boundaries:

1. **Binary Ninja to plugin:** the plugin reads the primary function and only
   the selection/relationship/reference packs explicitly enabled by the user.
2. **Plugin to local harness:** the prompt is sent through stdin to the exact
   configured executable.
3. **Harness to provider service:** authentication, transport, retention, and
   account policy are controlled by the external CLI/provider.
4. **Provider output to Qt:** Markdown is imported with
   `QTextDocument.MarkdownNoHTML`, so the parser never produces an HTML block
   or span and a provider tag can only render as inert literal text. Generic
   links are not opened; validated address citations become internal Binary
   Ninja navigation actions and unresolved addresses remain inert.
5. **Transcript to local storage:** persistence is off by default. When enabled,
   a bounded JSON record is stored under Binary Ninja's user directory using a
   path-free content fingerprint, never a provider credential or source path.

Version `0.9.0` does not write to the BNDB. Its package split is also a trust
boundary: `core/` and `application/` cannot
import Binary Ninja, Qt, subprocess, or network modules, and `providers/`
cannot import Binary Ninja or Qt. Contract tests enforce those restrictions.

## Enforced safeguards

- Explicit Ask or Explain action before dispatch.
- Binary base filename only; the full path is omitted.
- Exact pre-dispatch context preview and a deterministic combined character cap.
- Current-function context by default; every additional pack is opt-in and has
  explicit item-count/per-function limits.
- Prompts on stdin rather than process command lines.
- No direct access to provider credential stores.
- Claude Code tools, Chrome integration, slash commands, and session
  persistence disabled.
- Codex ephemeral execution in a read-only sandbox with user rules and config
  ignored.
- Ollama prompt history disabled for the child process and thinking hidden.
- Concurrent pipe draining, timeout, cancellation, and an 8 MB combined output
  ceiling.
- Main-thread-only UI updates and liveness checks for late callbacks.
- Optional transcript persistence is schema-versioned, limited to 200 messages
  and 8 MB, atomically replaced, and deleted through **Clear**.
- Provider comparison reuses one frozen context snapshot for both adapters.
- No symbol, type, comment, analysis, or database mutation.
- One validated semantic version sourced from `plugin.json`; invalid version
  metadata fails plugin import instead of silently reporting a different build.

## Not guaranteed

- Model output is not verified and may be incorrect or unsafe.
- Provider services and CLIs may retain data or collect telemetry according to
  their own policies.
- A model suggestion or catalog entry does not guarantee account access.
- The plugin cannot protect data after it is submitted to the chosen provider.
- Context preview shows exactly what the provider receives, but Axio Analyst
  does not automatically identify or redact secrets embedded in decompilation,
  strings, symbols, or user questions.

Use only providers approved for the binary being analyzed. Verify important
claims against IL addresses and independent evidence.

## Future security gates

Direct HTTP/API-key/OAuth support requires an OS credential-store broker,
redacted diagnostics, in-memory access tokens, and explicit endpoint trust.
Portable/collaborative workspaces still require encryption, migration, and
retention decisions beyond the bounded local transcript. BNDB write features
require validated proposed operations, review, one undoable
transaction, and an audit record. These are design gates, not optional cleanup.

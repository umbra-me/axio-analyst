# Security policy

## Supported version

Axio Analyst is pre-release. Only the latest development version on `main` is
currently supported. A versioned support table will be added when tagged
releases begin.

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

1. **Binary Ninja to plugin:** the plugin reads the selected function's typed
   metadata and HLIL after explicit user action.
2. **Plugin to local harness:** the prompt is sent through stdin to the exact
   configured executable.
3. **Harness to provider service:** authentication, transport, retention, and
   account policy are controlled by the external CLI/provider.
4. **Provider output to Qt:** raw HTML is escaped before Markdown presentation;
   transcript links are not opened.

Version `0.7.0` does not write to the BNDB and does not persist conversations.

## Enforced safeguards

- Explicit Ask or Explain action before dispatch.
- Binary base filename only; the full path is omitted.
- Current-function context only, with configurable deterministic truncation.
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
- No symbol, type, comment, analysis, or database mutation.

## Not guaranteed

- Model output is not verified and may be incorrect or unsafe.
- Provider services and CLIs may retain data or collect telemetry according to
  their own policies.
- A model suggestion or catalog entry does not guarantee account access.
- The plugin cannot protect data after it is submitted to the chosen provider.
- The current version has no per-request redaction preview beyond the visible
  disclosure and context limit.

Use only providers approved for the binary being analyzed. Verify important
claims against IL addresses and independent evidence.

## Future security gates

Direct HTTP/API-key/OAuth support requires an OS credential-store broker,
redacted diagnostics, in-memory access tokens, and explicit endpoint trust.
Persistent workspaces require encryption/retention/export decisions. BNDB write
features require validated proposed operations, review, one undoable
transaction, and an audit record. These are design gates, not optional cleanup.

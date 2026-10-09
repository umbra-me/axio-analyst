# Binary Ninja verification results — unfilled template

Plan: [manual verification](manual-verification.md).
Prepared: 2026-10-09. This file contains no observed result.
Copy it into your local notes and replace the placeholders; keep private paths,
credentials, account identifiers, and unrelated binary content out of the reply.

## Run identity

- Observed date/time/timezone: `<fill after running>`
- Tester: `<fill>`
- Axio source commit: `<git rev-parse HEAD>`
- Working tree changes affecting the run: `<describe, or none>`
- Source / installed metadata version: `<fill both>`
- Installer status and exit code: `<fill>`
- Binary Ninja Personal build: `<fill>`
- OS / architecture: `<fill>`
- Demo executable SHA-256: `<fill>`
- Selected function name / start: `<fill>`
- Context options / cap: `<fill>`
- Timeout / history preference: `<fill>`
- Other test BinaryView, if used: `<harmless description; no private path>`

| Provider | CLI version | Model | Effort | Tested or reason not run |
| --- | --- | --- | --- | --- |
| Claude Code | `<fill>` | `<fill>` | `<fill>` | not run |
| Codex | `<fill>` | `<fill>` | `<fill>` | not run |
| Ollama Cloud | `<fill>` | `<fill>` | `<fill>` | not run |

## Case ledger

Use `pass`, `fail`, `blocked`, or `not run`. Add separate rows when a case has
multiple stages. Do not change a status until you have observations to support it.

| Case | Variant / stage | Status | Receipt or reason |
| --- | --- | --- | --- |
| G00 | install / registration / baseline | not run | `<fill>` |
| G01 | 260 / 300 / 520 px; focus / scope / Settings | not run | `<split rows>` |
| G02 | Apply / Revert / provider choices / invalidation | not run | `<split rows>` |
| G03 | primary / types / neighbours / selection / all / cap | not run | `<split rows>` |
| G04 | Claude Code smoke / Ctrl+Enter | not run | `<fill>` |
| G04 | Codex smoke / Ctrl+Enter | not run | `<fill>` |
| G04 | Ollama Cloud smoke / Ctrl+Enter | not run | `<fill>` |
| G05 | Explain / each of four suggestions | not run | `<split rows>` |
| G06 | Claude scrolling / pre-output / mid-stream Stop | not run | `<split rows>` |
| G06 | Codex scrolling / lifecycle Stop | not run | `<split rows>` |
| G06 | Ollama scrolling / pre-output / mid-stream Stop | not run | `<split rows>` |
| G07 | Claude primary; Codex comparison | not run | `<fill>` |
| G07 | Codex primary; Ollama comparison | not run | `<fill>` |
| G07 | Ollama primary; Claude comparison | not run | `<fill>` |
| G07 | secondary failure / cancellation / No comparison | not run | `<split rows>` |
| G08 | raw tokens / code / HTML / valid / invalid / generic | not run | `<split rows>` |
| G09 | export dialog cancel / completed / cancelled export | not run | `<split rows>` |
| G10 | history Off / settings after full restart | not run | `<fill>` |
| G11 | completed response after full restart | not run | `<fill>` |
| G12 | cancelled before output after full restart | not run | `<fill>` |
| G12 | cancelled partial output after full restart | not run | `<fill>` |
| G13 | disable / reopen / re-enable / reopen | not run | `<fill>` |
| G14 | Clear / empty state / no restore after restart | not run | `<fill>` |
| G15 | same-binary cursor / replacement / preview / close | not run | `<split rows>` |
| G16 | each missing executable / recovery / timeout | not run | `<split rows>` |
| G17 | catalog / fallback / supersession / close | not run | `<split rows>` |
| G18 | theme / mark / About / read-only / shutdown | not run | `<split rows>` |

## Detailed receipt — duplicate for each result

```text
Case and variant:
Observed date/time/timezone:
Provider / CLI version / model / effort:
Function / address / options / cap / history:
Unique request marker:
Steps actually executed:
Observed phase/status sequence:
Observed response / footer / finding hash (public demo only):
Timing measured and how measured:
Before/after restart or navigation evidence, if applicable:
Raw Markdown tokens actually returned, if applicable:
Child PID / exit observation, if checked:
Screenshot/export/log reference (local basename; sanitized):
Expected behavior that matched:
Mismatch, exact sanitized error, or reason blocked:
Untested stages and limits of this observation:
Status: not run
```

## Final state and unresolved gates

- Original settings restored through Apply: `<fill>`
- Final history preference: `<fill>`
- Demo history/export retained or deliberately cleared: `<fill>`
- Test instance closed / other work preserved: `<fill>`
- Unexpected symbol/type/comment/save changes: `<fill>`
- Cases still not run, with reasons: `<fill>`
- Codex snapshot-only confinement: **open; GUI smoke tests cannot close it**
- Windows Job Object attachment/descendant containment: **unverified unless a
  separate platform-specific receipt is supplied**
- Markdown image/resource-loading policy: **unverified by this plan**
- Sampled identity aliases: **documented limitation; no format change**

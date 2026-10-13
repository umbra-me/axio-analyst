# Axio Analyst 0.9.1

## Source publication update — 2026-10-14

The owner authorized publication of the four preparation commits on `main`,
through `da0b34d98fdb290b27e512e122e3de88b6af687f`; the remote head was
verified. Earlier local/unpushed descriptions below are historical. This is
source publication only: no release tag, host installation, community submission
or workspace pin promotion was performed. Binary Ninja GUI registration,
minimum-host/platform compatibility and the provider/rendering acceptance gates
remain open; follow the existing release checklist before tagging a release.

**Release notes draft, prepared October 10, 2026.** `0.9.1` is the version
selected by the maintainer. Source metadata reports `0.9.1`.
This draft has not been published and does not establish live acceptance.
See the [release preparation](release-preparation.md) before using these notes.

Axio Analyst brings provider-neutral AI assistance into Binary Ninja for
reverse engineers investigating functions and checking hypotheses. Preview
bounded, address-labelled context, then ask Claude Code, Codex, or Ollama Cloud
to explain it or compare answers. The plugin stays read-only, keeps extra
context and local history opt-in, and leaves authentication with your CLI.

## Changes since 0.9.0

- Keep cancellation and timeouts active while a child is blocked on stdin or
  remains alive after closing its output pipes. Bound queued output, use a
  unique temporary directory for each run, and attempt process-tree cleanup
  on completion and failure.
- Reject Codex replies from failed turns or turns without `turn.completed`.
  Explicitly disable its shell/image tools and web search; the confidentiality
  limitation below still applies.
- Discard stale analysis and preview callbacks after binary replacement,
  settings changes, or supersession. Preserve completed primary text,
  findings, and usage when a comparison's second request is cancelled.
- Collect HLIL lazily with instruction/traversal ceilings and visible
  truncation. Share the same three-caller/five-callee selection between
  neighbourhood context and relevant types.
- Keep raw streamed chunks with a literal live preview capped at 64,000
  characters and a visible notice. Render the full retained Markdown once at
  completion, failure, or cancellation with HTML disabled.
- Supervise local Ollama model discovery with a 10-second deadline and 1 MB
  output cap; discard results superseded by executable changes.
- Add explicitly **unverified** findings with context provenance. New local
  conversation records use schema 2; schema 1 remains readable. Persistence
  stays off by default and exports retain the unverified status.
- Simplify the sidebar and Settings, add the painted product mark, preserve
  fenced-code punctuation, and wrap long code blocks. The README now has a
  quick start, a security summary, and pending real capture slots.

No development or runtime dependency was added for these fixes. Process-tree
support uses the Python standard library; optional Qt tests use Binary Ninja's
existing bundle. The project is maintained by
[Kian (Zenco)](https://github.com/notzenco) and licensed under MIT.

## Verification evidence

The [October 9 source checkpoint](https://github.com/umbra-me/axio-analyst/blob/main/docs/change-set-2026-10-09.md)
records 121 passing stock-Python tests and nine optional Qt skips; the separate
bundled-Qt run passed all 130 tests. Compileall, metadata, runtime-manifest and
installer contracts also passed. Harmless children, host fakes, and unshown Qt
widgets exercised the regression paths; these results are not provider
benchmarks or Binary Ninja GUI acceptance.

On October 10, the prepared `0.9.1` metadata and presentation/release changes
passed the stock suite again (121 passes, nine optional Qt skips), compileall,
metadata/runtime-version and license checks, relative documentation links,
whitespace, and syntax checks of the future tag/push commands. Those commands
were not executed. Runtime Python, tools and tests were unchanged by preparation.

The subsequent metadata-submission contract brought the October 10 stock suite
to 131 tests: 122 passes and nine optional Qt skips. The pinned Vector 35
validator and an isolated 36-file copier install passed; these do not establish
actual Extensions-manager installation or minimum-build/platform compatibility.

The latest recorded real-host receipt is
[September 5](https://github.com/umbra-me/axio-analyst/blob/main/docs/gui-verification.md).
It predates the October fixes. The
[manual verification plan](https://github.com/umbra-me/axio-analyst/blob/main/docs/manual-verification.md)
is prepared; no new user observations have been reported.

## Known limitations and pending release gates

- **Codex snapshot-only confidentiality is unproven.** Read-only execution and
  disabled shell/image/web tools do not establish isolation from unrelated
  readable files or globally disable independent tools.
- Windows Job Object cleanup has not been exercised. Attachment follows
  process launch, POSIX descendants can escape their group, and OS cleanup
  failures remain possible. Lifecycle supervision is not a security sandbox.
- HTML-disabled Markdown is not a validated image/resource-loading policy.
- Sampled conversation identities can alias different binaries. Enabled local
  history contains sensitive message text and supplied context excerpts.
- Live installation, provider switching/comparison, mid-stream cancellation,
  successful-response persistence, restart and narrow keyboard interaction
  still need receipts for the release candidate.
- Python cannot interrupt a blocked OS process-creation call or an individual
  Binary Ninja analysis/property call. Context limits cover item text, not
  prompt instructions, metadata or the question.
- The [community submission audit](community-submission-audit.md) passes metadata
  validation and an isolated copier layout; minimum-build, platform and actual
  manager acceptance remain open. Screenshots/GIF remain pending captures.

See the [security policy](https://github.com/umbra-me/axio-analyst/blob/main/SECURITY.md),
[provider contracts](https://github.com/umbra-me/axio-analyst/blob/main/docs/providers.md)
and [changelog](https://github.com/umbra-me/axio-analyst/blob/main/CHANGELOG.md)
for the detailed boundaries and change history. These links describe the
intended published documents; the local preparation commits are not pushed yet.

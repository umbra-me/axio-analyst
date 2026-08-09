# Axio Analyst handoff

Last updated: 2026-08-10 (third pass: real-host GUI verification)

## Repository identity

- Product: **Axio Analyst**
- Package and Binary Ninja plugin directory: `axio_analyst`
- Binary Ninja settings group: `axioAnalyst`
- Repository: `https://github.com/umbra-me/axio-analyst`
- Default branch: `main`
- Licence: MIT
- Source version: `0.9.0`
- Published source version: `0.9.0`
- Last live-installed version: `0.9.0`

This standalone repository is the product source of truth. A separate personal
Binary Ninja configuration repository may mirror runtime files for workstation
synchronization, but product code and maintained documentation belong here.

## Implemented source scope

Version `0.9.0` extends the read-only workflow with:

- exact context preview and a frozen per-request snapshot;
- primary-function HLIL by default plus opt-in selection, three direct callers,
  five direct callees, twenty referenced strings/imports, and relevant types;
- deterministic total budgeting, stable ordering, deduplication, and visible
  per-item/bundle truncation;
- validated internal navigation for `0x` evidence citations and inert unresolved
  or generic links;
- off-by-default schema-version-1 local conversation restoration, bounded to
  200 messages/8 MB, with atomic replacement, Clear deletion, and Markdown
  export;
- a path-free BinaryView content fingerprint for transcript association;
- qualitative two-provider comparison over exactly one frozen prompt;
- measured latency/character accounting plus provider-reported Claude and
  Codex token/cache metadata and Claude cost metadata;
- updated source metadata and Binary Ninja version surfaces for `0.9.0`.

The existing Claude Code, Codex, and Ollama Cloud adapters remain supervised,
stdin-only, credential-neutral, cancellable, and bounded. No code path mutates
names, types, comments, analysis, or BNDB state.

## Unreleased work on top of 0.9.0

The sidebar was redesigned and the product acquired an original mark. The
version is unchanged; these entries sit under `Unreleased` in the changelog.

- `ui/branding.py` paints the Axio Analyst mark (a split diamond: one bounded
  context read more than one way) and a thirteen-glyph action set on a shared
  24-unit grid. Nothing is shipped as an asset, so the runtime manifest gained
  one Python module and the installer gained no binary file.
- The chat surface went through two passes. The first dropped four framed boxes
  to one; the second reduced the resting layout to two bands, one header row
  and one composer. Explain, Compare, Export, Clear, and the version live in
  the header overflow menu. The composer's scope chip carries the disclosure,
  naming the function and appending `+N` for opt-in packs. An empty state names
  the function, architecture, and configured provider above four suggested
  questions. The status line is hidden until it has something to report, and
  each answer's metadata, evidence, and unresolved citations share one footer
  line.
- Settings replaced four group boxes with flat sections that collapse behind
  summaries of their staged values, stack labels above fields when narrow, and
  reserve height for wrapped guidance text.
- Provider HTML is now inerted by `QTextDocument.MarkdownNoHTML` at import
  rather than by escaping the source string. Escaping was leaking `&gt;`,
  `&lt;`, and `&amp;` into every fenced code block. Imported code blocks are
  also allowed to wrap, which removes the transcript's horizontal scrollbar at
  realistic dock widths.

Both rendering changes were verified empirically against Binary Ninja's own
PySide6 6.11.1 and Qt 6 before they were adopted: `<img src=x onerror=...>` and
`<script>` serialise as `&lt;img ...&gt;` literal text, while `>`, `&&`, and
`<` survive intact inside fenced code.

## Architecture in one pass

```text
Binary Ninja function, selection, and visible pack options
  -> host/context.py builds one bounded ContextBundle
  -> ui/sidebar.py previews the exact frozen snapshot
  -> application/analyze.py builds one provider-neutral prompt
  -> providers/ supervises the primary and optional comparison CLI
  -> host/task.py returns results through execute_on_main_thread
  -> core/evidence.py validates address citations against the BinaryView
  -> ui/transcript.py renders sanitized Markdown and internal anchors
  -> optional application/conversations.py atomically stores bounded messages
```

`core/`, `application/`, and `providers/` remain importable without Binary
Ninja. The host owns live Binary Ninja objects and user-directory selection;
the UI owns Qt widgets and user-triggered export/navigation.

## Security and data boundary

Preserve these properties:

- dispatch occurs only after explicit Ask or Explain;
- the primary function is the only default context item;
- every extra pack is visibly opt-in, direct rather than recursive, and bounded;
- the exact context is previewable and excludes source paths, whole binaries,
  BNDB files, and arbitrary unrelated functions;
- prompts stay off process command lines and credentials stay inside each CLI;
- Claude tools/session persistence remain disabled; Codex remains ephemeral,
  read-only, and isolated from user config/rules; Ollama child history remains
  disabled;
- raw provider HTML is inerted by the Markdown parser, generic links are inert,
  and restored evidence is revalidated rather than trusted from disk;
- conversation persistence is off by default and excludes prompts, context
  snapshots, paths, credentials, and raw binary bytes;
- no BNDB mutation is implemented.

Future HTTP/OAuth adapters still require an OS credential broker. Future
Binary Ninja writes still require validated proposed operations, a visible
review diff, one undoable transaction, and an audit record.

## Verification snapshot

Source-tree checks completed again on 2026-08-10 after the live GUI pass:

- `python -m unittest discover -s tests -t .`: 55 tests passed;
- `python -m compileall` over runtime, tools, and tests: passed;
- `plugin.json` parsed and reported `Axio Analyst 0.9.0`;
- repository contracts passed for the root-only entry module, package
  dependency boundaries, semantic-version surfaces, and complete runtime
  manifest;
- relative links across the maintained Markdown set were checked and resolved;
- the isolated development-installer contract copied the nested runtime and
  reported it current;
- the C++ demo fixture configured and built successfully with MSVC;
- `git diff --check` passed.

The published `0.9.0` plugin loads in a real Binary Ninja GUI. Earlier isolated
demo instances verified the previous Chat layout, visible version, dedicated
Context workspace, narrow Settings forms, saved provider executable paths, and
clean startup. A user-triggered Codex Explain request also completed
successfully and reported usage metadata.

The redesigned runtime and mark were checked again in Binary Ninja Personal
`5.4.10350-dev` on the `samples/demo` fixture. The registration log reported
`Axio Analyst v0.9.0: plugin registration complete.` with no sidebar error or
Python traceback. The live non-network check confirmed:

- the active split-diamond mark, two-band resting layout, empty state, four
  suggestions, composer scope chip, keyboard hint, send glyph, and hidden idle
  status;
- version `0.9.0` in the registration log, Settings introduction, and overflow
  menu;
- function tracking from `main` to `sub_140001000`, including header/address
  replacement and invalidation of the prior preview;
- a one-item, 3,275-character primary preview and an eight-item,
  14,195-character all-pack preview with no source path;
- staged Settings summaries and expansion of the 270-second timeout and
  65,000-character context limit without applying a change;
- no provider dispatch, BNDB creation, symbol/type/comment mutation, or tracked
  repository change.

The exact evidence and remaining checks are maintained in
[`gui-verification.md`](gui-verification.md). Binary Ninja does not hot-reload
Python plugins, so the check used a separate `-n` instance and closed only that
instance afterward. Binary Ninja's own command-line help separately confirmed
that `files` are positional arguments and `-l, --debug-log <file>` selects a
log destination rather than a binary to open.

Layout at other dock widths was reviewed separately with a Qt harness that
loads the real `ui/sidebar_view.py` under Binary Ninja's own Python 3.13 and
PySide6 6.11.1, stubs `binaryninja.Settings`, and captures unmapped widgets
with `QWidget.grab()`. Binary Ninja's Qt bundle ships only `qwindows.dll`, so
`QT_QPA_PLATFORM=offscreen` is unavailable and the harness must grab rather
than run headless. It covers 260-560 pixels including the suggestion empty
state, the composer scope chip and its `+N` disclosure, the one-line answer
footer, and expanded/collapsed Settings sections.

Still unverified by hand in the redesigned runtime: narrow-width tab focus and
`Ctrl+Enter`; suggestion/provider dispatch; status reveal and auto-hide;
streaming, cancellation, evidence navigation, comparison, export, persistence,
Clear deletion, restart, live theme switching, inactive mark tint, and the
About command. No provider was invoked during the latest pass because the test
did not have fresh authorization to send the fixture context externally.

## Current live-install state

The redesigned runtime is installed in the confirmed Binary Ninja user plugin
directory with the user's explicit permission. `plugin_dev.py status` reports
`Axio Analyst is current` and the installed metadata reports
`Axio Analyst 0.9.0`. The install added one file, `ui/branding.py`, and
replaced five `ui/` modules; `--prune-obsolete` was not used and no unrelated
destination content was removed or modified. The Codex and Ollama executable
overrides remain saved in Binary Ninja user settings.

Verification and command-line probe instances started specifically for these
checks were closed afterward. Pre-existing user Binary Ninja sessions were
inventoried and left running.

Binary Ninja's separate Windows application updater currently reports
**Update Failed: Updater is not valid.** The pending cache's content-addressed
payload hashes match, and its `update.exe` is identical to the installed copy;
both have valid Vector 35 Authenticode signatures. The plugin still registers
and the installed runtime still reports current, so no evidence connects this
failure to Axio Analyst. Follow
[`troubleshooting.md`](troubleshooting.md#binary-ninja-reports-updater-is-not-valid)
and use a fresh eligible installer from Vector 35 if retrying the self-updater
fails. The cache and application installation were not changed during this
assessment.

Binary Ninja does not hot-reload Python plugins, so any further runtime change
needs a restart or a fresh `-n` instance. Do not broadly clean the Binary Ninja
user directory; it contains licences, settings, symbols, themes, and unrelated
plugins. Do not stop existing Binary Ninja sessions merely to refresh the
development copy; coordinate a normal restart with the user.

## Published state and next steps

The `0.9.0` implementation and its documentation were published as separate
logical commits. The redesign that follows it was published on `main` as four
more: the mark and glyph set, the Markdown rendering fixes, the sidebar
rebuild, and this documentation pass. Each was verified to pass the suite
independently in a throwaway worktree, so the history stays bisectable. The
changes sit under `Unreleased` in the changelog; the source version is still
`0.9.0` and no tag was created. The Sidekick inventory is reference research;
it does not imply code reuse or a compatibility commitment.

This third documentation pass adds the dated real-host report, replaces stale
manual-check claims with the completed/deferred split, and records the separate
Binary Ninja updater failure and supported recovery path. It changes no runtime
module or plugin metadata.

Next product and verification steps:

1. Use a deterministic local harness for streaming, cancellation, Markdown,
   evidence, export, Clear, and persistence cases that do not need a real
   provider.
2. Complete the remaining narrow-width, keyboard, theme, About, restart, and
   explicitly authorized provider/Compare checks in `gui-verification.md`.
3. Resolve the separate Binary Ninja self-updater failure through Vector 35's
   supported installer path; do not alter the plugin or user directory as a
   workaround.
4. Fix any host-only issues, rerun all verification, and refresh this handoff.
5. Decide whether the redesign warrants a version bump, then decide the
   tagged-release and Binary Ninja plugin-manager publication path; keep hosted
   CI disabled unless it is explicitly approved.

Remaining product phases are direct HTTP/credential brokerage, structured
claim provenance, portable workspaces, indexing/tool brokerage, and reviewable
BNDB transformations. Their gates remain in `roadmap.md`.

## Resume commands

```powershell
git status --short --branch
python -m unittest discover -s tests -t .
python -m compileall -q __init__.py application core host providers ui tools tests
python -c "import json,pathlib; print(json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))['version'])"
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

# Axio Analyst handoff

Last updated: 2026-08-10 (second pass: sidebar redesign and product mark)

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
- The chat surface dropped from four framed boxes to one. Export and Clear
  moved to a header overflow menu; the comparison provider moved into the
  **Ask** menu. The **Context** button carries the scope disclosure as
  `Context +N` and keeps the count below a 300-pixel dock width.
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

Source-tree checks completed on 2026-08-10 after the redesign:

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
demo instances verified the then-current Chat layout, visible version,
dedicated Context workspace, narrow Settings forms, saved provider executable
paths, and clean startup. A user-triggered Codex Explain request also completed
successfully and reported usage metadata.

The redesigned sidebar and the new mark were installed and loaded in a real
Binary Ninja `5.4.10350-dev` GUI on the `samples/demo` fixture. A debug log
(`binaryninja.exe -n -d -l <file>`) recorded
`Axio Analyst v0.9.0: plugin registration complete.` with no sidebar
registration error and no Python traceback, and a window capture confirmed:

- the split-diamond mark rendering in Binary Ninja's own right rail under its
  active blue tint, legible beside the stock rail glyphs;
- the flat header scope line, dim detail line, and right-aligned version;
- the frameless transcript, prompt, single action row (`Context`, `Explain`,
  `Ask`), and the merged status strip reading
  `Ready` / `Codex - gpt-5.6-sol - medium`;
- `Ask` correctly disabled while the prompt is empty.

Layout at other dock widths was reviewed separately with a Qt harness that
loads the real `ui/sidebar_view.py` under Binary Ninja's own Python 3.13 and
PySide6 6.11.1, stubs `binaryninja.Settings`, and captures unmapped widgets
with `QWidget.grab()`. Binary Ninja's Qt bundle ships only `qwindows.dll`, so
`QT_QPA_PLATFORM=offscreen` is unavailable and the harness must grab rather
than run headless. It covers 260-560 pixels including the narrow action row,
the `Context +N` disclosure, and expanded/collapsed Settings sections.

Still unverified by hand: menu popups (overflow, `Compare with`), tab focus
order, live theme switching, and the standing checklist items in
`development.md` for context-preview contents, evidence navigation,
comparison, persistence, export, Clear deletion, cancellation, and
Ollama/Claude requests.

## Current live-install state

The redesigned runtime is installed in the confirmed Binary Ninja user plugin
directory with the user's explicit permission. `plugin_dev.py status` reports
`Axio Analyst is current` and the installed metadata reports
`Axio Analyst 0.9.0`. The install added one file, `ui/branding.py`, and
replaced five `ui/` modules; `--prune-obsolete` was not used and no unrelated
destination content was removed or modified. The Codex and Ollama executable
overrides remain saved in Binary Ninja user settings.

The Binary Ninja process inventoried at the start of this session exited on its
own before the install; it was never stopped or restarted by tooling. The
verification instance was started separately with `-n` so it could not disturb
an existing session.

Binary Ninja does not hot-reload Python plugins, so any further runtime change
needs a restart or a fresh `-n` instance. Do not broadly clean the Binary Ninja
user directory; it contains licences, settings, symbols, themes, and unrelated
plugins.

## Published state and next steps

The `0.9.0` implementation and its documentation were published as separate
logical commits. The redesign that follows it is **uncommitted** in the working
tree and has not been pushed. The Sidekick inventory is reference research; it
does not imply code reuse or a compatibility commitment.

Next product and verification steps:

1. Confirm the overflow and `Compare with` menus, tab focus order, and theme
   switching by hand in the installed GUI.
2. Complete the remaining expanded GUI checklist with `samples/demo` and test
   only providers the user authorizes.
3. Fix any host-only issues, rerun all verification, and refresh this handoff.
4. Commit the redesign once it is accepted, then decide the tagged-release and
   Binary Ninja plugin-manager publication path; keep hosted CI disabled unless
   it is explicitly approved.

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

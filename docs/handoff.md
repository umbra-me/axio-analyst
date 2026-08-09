# Axio Analyst handoff

Last updated: 2026-08-10

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
- raw provider HTML is escaped, generic links are inert, and restored evidence
  is revalidated rather than trusted from disk;
- conversation persistence is off by default and excludes prompts, context
  snapshots, paths, credentials, and raw binary bytes;
- no BNDB mutation is implemented.

Future HTTP/OAuth adapters still require an OS credential broker. Future
Binary Ninja writes still require validated proposed operations, a visible
review diff, one undoable transaction, and an audit record.

## Verification snapshot

Source-tree checks completed on 2026-08-10:

- `python -m unittest discover -s tests -t .`: 53 tests passed;
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

The `0.9.0` plugin now loads in a real Binary Ninja GUI. Fresh isolated demo
instances verified the compact Chat layout, visible version, dedicated Context
workspace, narrow Settings forms, saved provider executable paths, and clean
startup. A user-triggered Codex Explain request also completed successfully and
reported usage metadata. The full checklist in `development.md` is still open
for context-preview contents, evidence navigation, comparison, persistence,
export, Clear deletion, cancellation, and Ollama/Claude requests.

## Current live-install state

The manifest-owned `0.9.0` runtime is installed in the confirmed Binary Ninja
user plugin directory. An independent status check reports `Axio Analyst is
current`, and the installed metadata reports `Axio Analyst 0.9.0`. The Codex
and Ollama executable overrides are saved in Binary Ninja user settings and
render correctly on the Settings page. Unrelated destination content was not
removed or modified.

The refreshed UX was loaded in separate `--new-instance` demo processes so the
user's existing analysis session was not restarted. Those isolated processes
were closed cleanly after inspection. The `0.9.0` implementation, tests,
maintained documentation, and dated Sidekick capability inventory are
published on `main`.

Do not describe `0.9.0` as fully host-verified until the remaining manual
checklist passes. Do not broadly clean the Binary Ninja user directory; it
contains licences, settings, symbols, themes, and unrelated plugins.

## Published state and next steps

The `0.9.0` implementation and its documentation were published as separate
logical commits. At the publication check, local `main` matched `origin/main`
and the working tree was clean. The Sidekick inventory is reference research;
it does not imply code reuse or a compatibility commitment.

Next product and verification steps:

1. Complete the remaining expanded GUI checklist with `samples/demo` and test
   only providers the user authorizes.
2. Fix any host-only issues, rerun all verification, and refresh this handoff.
3. Decide the tagged-release and Binary Ninja plugin-manager publication path;
   keep hosted CI disabled unless it is explicitly approved.

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

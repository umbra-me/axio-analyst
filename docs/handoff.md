# Axio Analyst handoff

Last updated: 2026-08-09

## Repository identity

- Product: **Axio Analyst**
- Package and Binary Ninja plugin directory: `axio_analyst`
- Binary Ninja settings group: `axioAnalyst`
- Repository: `https://github.com/umbra-me/axio-analyst`
- Default branch: `main`
- Licence: MIT
- Current plugin version: `0.8.0`
- Publication posture: public for the current phase; private product services
  can be split later without moving provider credentials or proprietary user
  data into this repository.

This standalone repository is the product source of truth. A separate personal
Binary Ninja configuration repository may mirror the runtime files for local
workstation synchronization, but product implementation and maintained product
documentation belong here first.

## Implemented scope

Version `0.8.0` is a complete read-only current-function workflow:

- native right sidebar with Chat and Settings pages;
- cursor-following function context;
- one-click explanation and free-form questions;
- bounded, address-labelled HLIL prompts;
- Claude Code, Codex, and Ollama Cloud CLI adapters;
- per-provider model and reasoning selection;
- dynamic Ollama Cloud catalog discovery and local CLI fallback;
- streamed sanitized Markdown, stable scroll behavior, phase progress, elapsed
  time, cancellation, timeouts, and bounded process output;
- function menu commands that remain useful independently of the sidebar;
- a metadata-backed semantic version shown in the plugin manager, sidebar,
  Settings page, About command, and registration log;
- a stock-Python test suite, bounded development installer, and C++ fixture.

The product and all active identifiers are standardized on Axio Analyst. The
sidebar icon uses `AX`; no compatibility alias for an earlier package or
settings namespace is maintained.

## Architecture in one pass

```text
Binary Ninja function under cursor
  -> host/context.py renders bounded address-labelled HLIL
  -> application/analyze.py builds a provider-neutral request
  -> providers/ supervises one authenticated CLI
  -> host/task.py coalesces stream/progress callbacks
  -> execute_on_main_thread returns updates to ui/sidebar.py
  -> ui/transcript.py escapes and renders provider Markdown
```

`host/settings.py` is the only settings boundary. `host/registration.py`
registers two function actions, the sidebar-opening and About commands, and
then the Qt sidebar on a best-effort basis. `core/`, `application/`, and
`providers/` do not import Binary Ninja.

Provider processes run from a dedicated temp directory, receive prompts over
stdin, and drain stdout/stderr concurrently. The shared runner enforces the
configured timeout, cancellation, and an 8 MB output ceiling.

## Security and data boundary

Preserve these properties in every change:

- dispatch occurs only after an explicit Ask or Explain action;
- only base filename, function metadata, and bounded current-function HLIL are
  sent;
- the source path, full binary, BNDB, and unrelated functions are not sent;
- provider credentials remain inside the provider CLI;
- prompts are not exposed in process command-line arguments;
- Claude tools and persistence are disabled;
- Codex is ephemeral, read-only, and ignores user rules/configuration;
- Ollama prompt history is disabled for the child process;
- raw provider HTML is escaped and transcript links are not opened;
- no code path changes names, types, comments, analysis, or BNDB state.

Future direct API/OAuth support needs an OS credential-store broker. Future
Binary Ninja writes need validated proposed operations, a visible review diff,
one undoable transaction, and an audit record. Neither should be bolted onto
the current adapter without those boundaries.

## Verification snapshot

Current checkout verification on 2026-08-09:

- `python -m unittest discover -s tests -t .`: 40 tests passed;
- `python -m compileall` over runtime, tools, and tests: passed;
- `plugin.json` JSON parsing and metadata tests: passed;
- repository contracts confirmed the root-only entry module, complete runtime
  manifest, and dependency restrictions on `core/` and `application/`;
- the development installer copied the nested runtime into an isolated
  temporary plugin directory, pruned only seeded known-obsolete modules, and
  reported it current;
- an additional dry run enumerated only manifest-owned runtime files;
- Binary Ninja Personal `5.4.10350-dev` loaded the installed package, exposed
  the `AX` sidebar icon, and visibly rendered `v0.8.0` in the sidebar header and
  `Axio Analyst v0.8.0` on the Settings page.

Before this package refactor, the flat `0.7.0` implementation had also passed
the C++ demo, companion configuration checks, and a real Binary Ninja Personal
`5.4.10303-dev` sidebar launch. Those earlier checks are historical evidence,
not host validation of the new package layout.

Installed provider CLI versions observed during the documentation pass:

- Claude Code `2.1.226`;
- Codex CLI `0.147.0`;
- Ollama `0.32.6`.

These versions are evidence for the current workstation, not minimum-version
guarantees. CLI output formats and flags can change; rerun parser and real
harness checks when upgrading them.

## Current live-install state

The package-based `0.8.0` runtime is installed at the confirmed user plugin
path. The development installer reports every manifest-owned file current, the
installed metadata reports `0.8.0`, and all nine obsolete flat modules were
removed while unrelated destination-only content was preserved. Binary Ninja
was closed throughout installation.

Binary Ninja Personal `5.4.10350-dev` subsequently loaded the installed sample
and Axio Analyst sidebar. The live GUI confirmed registration and the two
visible `0.8.0` version surfaces without dispatching a provider request or
changing settings. Binary Ninja was no longer running at the final process
check.

## Protected local state

- Do not remove or overwrite Binary Ninja's user directory broadly. It may
  contain a personal licence, settings, themes, symbols, and unrelated plugins.
- The development installer copies an explicit runtime allowlist. Its optional
  migration flag prunes only explicitly listed obsolete flat modules, never
  arbitrary destination-only files.
- Do not commit live `settings.json`, licences, keychains, provider credential
  stores, generated sample builds, proprietary binaries, BNDBs, or transcripts.
- Restart Binary Ninja after installing changed Python files; do not assume
  already-imported modules hot-reload safely.

## Next concrete work

1. Complete the remaining manual checklist in `development.md`, including one
   request through every available provider.
2. Capture only sanitized product screenshots after the `AX` icon and Axio
   Analyst naming are visibly confirmed.
3. Decide the first tagged release and Binary Ninja plugin-manager publication
   path; add hosted CI only when explicitly approved.
4. Begin Phase 1 with richer context preview and persistent local conversation
   storage before adding write operations.
5. Design direct HTTP adapters and OAuth/API-key storage around an OS
   credential broker rather than Binary Ninja settings.

The authoritative longer-term sequence remains in `roadmap.md`. Avoid
starting persistent storage, direct APIs, indexing, MCP tools, or BNDB mutation
as isolated features without first defining their data, consent, and migration
boundaries.

## Resume commands

From the repository root:

```powershell
git status --short --branch
python -m unittest discover -s tests -t .
python -m compileall -q __init__.py application core host providers ui tools tests
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

Launch Binary Ninja, inspect the registration log and version surfaces, open
`samples/demo/build/Release/axio_analyst_demo.exe`, and complete the manual GUI
checklist before describing the release as fully host-verified.

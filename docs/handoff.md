# Axio Analyst handoff

Last updated: 2026-08-09

## Repository identity

- Product: **Axio Analyst**
- Package and Binary Ninja plugin directory: `axio_analyst`
- Binary Ninja settings group: `axioAnalyst`
- Repository: `https://github.com/umbra-me/axio-analyst`
- Default branch: `main`
- Licence: MIT
- Current plugin version: `0.7.0`
- Publication posture: public for the current phase; private product services
  can be split later without moving provider credentials or proprietary user
  data into this repository.

This standalone repository is the product source of truth. A separate personal
Binary Ninja configuration repository may mirror the runtime files for local
workstation synchronization, but product implementation and maintained product
documentation belong here first.

## Implemented scope

Version `0.7.0` is a complete read-only current-function workflow:

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
- a stock-Python test suite, bounded development installer, and C++ fixture.

The product and all active identifiers are standardized on Axio Analyst. The
sidebar icon uses `AX`; no compatibility alias for an earlier package or
settings namespace is maintained.

## Architecture in one pass

```text
Binary Ninja function under cursor
  -> task.py renders bounded address-labelled HLIL
  -> prompts.py builds a provider-neutral request
  -> providers.py supervises one authenticated CLI
  -> task.py coalesces stream/progress callbacks
  -> execute_on_main_thread returns updates to sidebar.py
  -> rendering.py escapes raw HTML before Markdown presentation
```

`settings.py` is the only settings boundary. `registration.py` registers two
function actions, the sidebar-opening command, and then the Qt sidebar on a
best-effort basis. Provider and parser modules do not import Binary Ninja.

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

Verified on 2026-08-09:

- `python -m unittest discover -s tests`: 31 tests passed;
- `python -m compileall` over runtime, tools, and tests: passed;
- `plugin.json` JSON parsing and metadata tests: passed;
- development install status: current at the active Windows Binary Ninja user
  plugin directory;
- companion Binary Ninja configuration suite: 40 tests passed;
- companion configuration sync: 24 tracked files in sync;
- theme validation in the companion configuration repository: passed;
- C++ demo Release build and `--demo` execution: passed;
- active source/path scan: no superseded product-name identifiers remained.
- real Binary Ninja Personal `5.4.10303-dev` host: the demo binary was open and
  the native Axio Analyst sidebar was registered with its context, provider,
  transcript, prompt, Explain/Ask/Stop, status, and disclosure controls visible
  to the Windows accessibility tree.

Installed provider CLI versions observed during the documentation pass:

- Claude Code `2.1.226`;
- Codex CLI `0.147.0`;
- Ollama `0.32.6`.

These versions are evidence for the current workstation, not minimum-version
guarantees. CLI output formats and flags can change; rerun parser and real
harness checks when upgrading them.

## Current live-install state

Binary Ninja is currently running from the registered Windows installation and
the Axio Analyst sidebar is loaded. The live development copy differs from this
checkout only in `sidebar.py`: the checkout changes the generated sidebar icon
initials to `AX` and adds a regression test, while the already-running process
has the earlier module loaded.

Do not overwrite or restart the user's active Binary Ninja process. After it is
closed normally, run the development installer, relaunch Binary Ninja, and
visually confirm the `AX` icon. The rest of the sidebar registration is already
host-verified; the full multi-provider manual checklist remains the release
gate.

## Protected local state

- Do not remove or overwrite Binary Ninja's user directory broadly. It may
  contain a personal licence, settings, themes, symbols, and unrelated plugins.
- The development installer copies an explicit runtime allowlist and does not
  prune destination-only files.
- Do not commit live `settings.json`, licences, keychains, provider credential
  stores, generated sample builds, proprietary binaries, BNDBs, or transcripts.
- Restart Binary Ninja after installing changed Python files; do not assume
  already-imported modules hot-reload safely.

## Next concrete work

1. After Binary Ninja is closed normally, refresh the live development copy and
   relaunch it without disturbing the user directory.
2. Visually confirm the `AX` icon and complete the remaining manual checklist in
   `development.md`, including one request through every available provider.
3. Capture only sanitized product screenshots after the `AX` icon and Axio
   Analyst naming are visibly confirmed.
4. Decide the first tagged release and Binary Ninja plugin-manager publication
   path; add hosted CI only when explicitly approved.
5. Begin Phase 1 with richer context preview and persistent local conversation
   storage before adding write operations.
6. Design direct HTTP adapters and OAuth/API-key storage around an OS
   credential broker rather than Binary Ninja settings.

The authoritative longer-term sequence remains in `architecture.md`. Avoid
starting persistent storage, direct APIs, indexing, MCP tools, or BNDB mutation
as isolated features without first defining their data, consent, and migration
boundaries.

## Resume commands

From the repository root:

```powershell
git status --short --branch
python -m unittest discover -s tests
python -m compileall -q __init__.py models.py prompts.py providers.py `
  registration.py rendering.py settings.py settings_page.py sidebar.py `
  task.py tools tests
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

After Binary Ninja is closed normally, run the development installer, launch it
again, inspect the log, open `samples/demo/build/Release/axio_analyst_demo.exe`,
and complete the manual GUI checklist before describing the release as fully
host-verified.

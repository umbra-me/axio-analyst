# Development and release guide

## Repository layout

The repository root is also the importable Binary Ninja plugin package.

| Path | Responsibility |
| --- | --- |
| `__init__.py` | Host-aware plugin entry point; avoids importing Binary Ninja during stock-Python tests. |
| `models.py` | Provider-neutral context, configuration, result, cancellation, and error types. |
| `prompts.py` | Current-function prompt and deterministic HLIL truncation. |
| `providers.py` | CLI supervision, streaming parsers, catalog discovery, and provider factory. |
| `settings.py` | Registration and access for the `axioAnalyst.*` user settings. |
| `task.py` | Binary Ninja context rendering and `BackgroundTaskThread` lifecycle. |
| `rendering.py` | Escaping and Markdown conversion helpers independent of Binary Ninja. |
| `settings_page.py` | Qt6 staged settings UI. |
| `sidebar.py` | Qt6 chat UI, conversation state, discovery orchestration, progress, and cancellation. |
| `registration.py` | Plugin menu commands and best-effort sidebar registration. |
| `tests/` | Stock-Python tests with Binary Ninja/PySide stubs where required. |
| `tools/plugin_dev.py` | Exact runtime-file copier and drift checker. |
| `samples/demo/` | Harmless C++ reverse-engineering fixture. |
| `docs/` | Maintained product, architecture, operations, and handoff documentation. |

## Design constraints

- Binary Ninja 5.x is a Qt6 host. Use its bundled PySide6 modules; do not add a
  PySide2-only path.
- Keep `models.py`, `prompts.py`, `providers.py`, and `rendering.py` importable
  without Binary Ninja so provider logic remains testable on stock Python.
- Run provider work in `BackgroundTaskThread` and pipe readers. Return UI
  updates through `execute_on_main_thread`.
- Treat provider Markdown as untrusted and preserve raw-HTML escaping.
- Do not add provider credential access. Harness adapters delegate auth to the
  installed CLI.
- Preserve the version `0.7` read-only boundary. Any future BNDB writes require
  a separate preview, validation, transaction, and undo design.
- Do not add runtime, native, privileged, or paid dependencies without an
  explicit distribution decision.

## Local verification

Run from the repository root:

```powershell
python -m unittest discover -s tests
python -m compileall -q __init__.py models.py prompts.py providers.py `
  registration.py rendering.py settings.py settings_page.py sidebar.py `
  task.py tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
```

Run a focused test:

```powershell
python -m unittest `
  tests.test_axio_analyst.TestPromptConstruction.test_prompt_preserves_evidence_addresses
```

Check or install the live development copy:

```powershell
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
python tools/plugin_dev.py install `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

Build the sample on Windows:

```powershell
Push-Location samples/demo
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
Pop-Location
```

## Test coverage

The current suite covers:

- required repository/runtime files and plugin metadata;
- address preservation, default questions, and deterministic truncation;
- Claude Code, Codex, and Ollama command construction;
- supported Claude event-document/array/JSONL shapes;
- Codex event parsing and final-message extraction;
- Ollama local/cloud catalog parsing and cloud-tag normalization;
- executable validation, nonzero exits, timeout, cancellation, output limits,
  concurrent stdout/stderr draining, and streamed chunk delivery;
- raw-HTML escaping and transcript scroll restoration;
- development installer target naming, dry run, copy, and drift reporting.

Pure tests cannot validate `binaryninjaui`, widget placement, signal wiring, or
real host startup. Manual GUI verification is therefore required before a
release.

## Manual GUI checklist

1. Start a supported Binary Ninja build with user plugins enabled.
2. Confirm the log contains no Axio Analyst import or registration error.
3. Confirm the sidebar icon shows `AX` and opens the **Axio Analyst** widget.
4. Move between functions and confirm the context card follows the cursor.
5. Verify Chat and Settings keyboard navigation at narrow sidebar widths.
6. Apply and revert provider, model, effort, executable, timeout, and context
   settings.
7. Send one request through every provider available to the tester.
8. Confirm streaming behavior, manual-scroll preservation, progress, elapsed
   time, cancellation, error presentation, and transcript clearing.
9. Restart Binary Ninja and confirm persisted settings survive.
10. Confirm no symbol, type, comment, analysis, or BNDB state changed.

## Change workflow

1. Read `AGENTS.md` and the documentation owning the behavior being changed.
2. Inspect the working tree and preserve unrelated changes.
3. Keep provider/prompt/parser changes independent of Binary Ninja imports.
4. Add or update direct tests with the implementation.
5. Update README, reference docs, changelog, and handoff when their claims
   change.
6. Run the complete verification commands and manual GUI checks available in
   the environment.
7. Review the staged diff for secrets, generated binaries, user settings, and
   proprietary analysis material.
8. Use Conventional Commit subjects and do not bypass hooks or failed checks.

## Release checklist

1. Decide the semantic version and update `plugin.json`.
2. Move relevant `CHANGELOG.md` entries from Unreleased to a dated version.
3. Confirm `README.md`, provider contracts, settings reference, roadmap, and
   handoff describe the shipped behavior.
4. Run the test, compile, metadata, installer, sample, and manual GUI checks.
5. Confirm the runtime file list in `tools/plugin_dev.py` is complete.
6. Verify the repository contains no secrets, populated environment files,
   generated sample builds, provider transcripts, or BNDB files.
7. Tag the verified commit only after the release mechanism and Binary Ninja
   plugin-manager metadata have been decided.

There is currently no hosted CI or automated release workflow. Local
verification and a real Binary Ninja launch are the release gates.

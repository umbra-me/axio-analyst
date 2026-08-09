# Development and release guide

## Repository layout

The repository root is the importable Binary Ninja plugin package, but only
`__init__.py` contains runtime Python at that level. Implementation lives in
packages grouped by dependency boundary.

| Path | Responsibility |
| --- | --- |
| `__init__.py` | Host-aware entry point; does not import Binary Ninja during stock-Python tests. |
| `core/` | Serializable models, provider contract, prompts, and deterministic safety policies. |
| `application/` | Provider-neutral use cases operating on injected interfaces. |
| `providers/` | CLI supervision, streaming, provider adapters, catalog parsing, and factory. |
| `host/` | Binary Ninja context, settings, background tasks, model discovery, and registration. |
| `ui/` | Qt6 sidebar controller/view, settings page, transcript, progress, and Markdown safety. |
| `tests/unit/` | Pure unit tests arranged by runtime package. |
| `tests/contract/` | Repository layout, dependency-boundary, metadata, and installer contracts. |
| `tools/runtime_manifest.py` | Authoritative explicit allowlist of installed runtime files. |
| `tools/plugin_dev.py` | Bounded runtime copier and drift checker. |
| `samples/demo/` | Harmless C++ reverse-engineering fixture. |
| `docs/` | Maintained product, architecture, operations, and handoff documentation. |

## Design constraints

- Binary Ninja 5.x is a Qt6 host. Use its bundled PySide6 modules; do not add a
  PySide2-only path.
- Keep `core/`, `application/`, and `providers/` importable without Binary
  Ninja so provider logic remains testable on stock Python. `core/` and
  `application/` must also remain free of Qt, subprocess, and network imports.
- Run provider work in `BackgroundTaskThread` and pipe readers. Return UI
  updates through `execute_on_main_thread`.
- Treat provider Markdown as untrusted and preserve raw-HTML escaping.
- Do not add provider credential access. Harness adapters delegate auth to the
  installed CLI.
- Preserve the read-only boundary introduced in `0.7.0`. Any future BNDB
  writes require a separate preview, validation, transaction, and undo design.
- Do not add runtime, native, privileged, or paid dependencies without an
  explicit distribution decision.

## Local verification

Run from the repository root:

```powershell
python -m unittest discover -s tests -t .
python -m compileall -q __init__.py application core host providers ui tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
```

Run a focused test:

```powershell
python -m unittest `
  tests.unit.core.test_prompts.TestPromptConstruction.test_prompt_preserves_evidence_addresses
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
- injected application orchestration without a concrete provider dependency;
- runtime-manifest completeness and core/application dependency boundaries;
- semantic-version validation and all intended Binary Ninja version surfaces;
- development installer target naming, nested-file copy, drift reporting, and
  exact obsolete-module pruning without deleting unrelated files.

Pure tests cannot validate `binaryninjaui`, widget placement, signal wiring, or
real host startup. Manual GUI verification is therefore required before a
release.

## Manual GUI checklist

1. Start a supported Binary Ninja build with user plugins enabled.
2. Confirm the log contains the versioned Axio Analyst registration message and
   no import or registration error.
3. Confirm the sidebar icon shows `AX`, opens the **Axio Analyst** widget, and
   displays the same version as `plugin.json`.
4. Move between functions and confirm the context card follows the cursor.
5. Verify Chat and Settings keyboard navigation at narrow sidebar widths.
6. Apply and revert provider, model, effort, executable, timeout, and context
   settings.
7. Send one request through every provider available to the tester.
8. Confirm streaming behavior, manual-scroll preservation, progress, elapsed
   time, cancellation, error presentation, and transcript clearing.
9. Confirm the Settings introduction and About command display the same
   version as the sidebar.
10. Restart Binary Ninja and confirm persisted settings survive.
11. Confirm no symbol, type, comment, analysis, or BNDB state changed.

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

1. Decide the semantic version and update `plugin.json`, the single runtime
   version source.
2. Move relevant `CHANGELOG.md` entries from Unreleased to a dated version.
3. Confirm `README.md`, provider contracts, settings reference, roadmap, and
   handoff describe the shipped behavior.
4. Run the test, compile, metadata, installer, sample, and manual GUI checks.
5. Confirm the sidebar, Settings page, About command, and registration log all
   read the version through `core/version.py`.
6. Confirm the runtime file list in `tools/runtime_manifest.py` is complete.
7. Verify the repository contains no secrets, populated environment files,
   generated sample builds, provider transcripts, or BNDB files.
8. Tag the verified commit only after the release mechanism and Binary Ninja
   plugin-manager metadata have been decided.

There is currently no hosted CI or automated release workflow. Local
verification and a real Binary Ninja launch are the release gates.

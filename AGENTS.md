# Axio Analyst repository instructions

## Commands

- Run tests: `python -m unittest discover -s tests -t .`
- Run one test: `python -m unittest tests.unit.core.test_prompts.TestPromptConstruction.test_prompt_preserves_evidence_addresses`
- Compile Python: `python -m compileall -q __init__.py application core host providers ui tools tests`
- Validate metadata: `python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"`
- Check a development install: `python tools/plugin_dev.py status --plugins-dir <Binary-Ninja-plugins-dir>`
- Install a development copy: `python tools/plugin_dev.py install --plugins-dir <Binary-Ninja-plugins-dir>`
- Build the Windows demo: `cd samples/demo; ./build.ps1`

## Architecture

- The root `__init__.py` is the loadable Binary Ninja entry point; runtime implementation lives in first-level packages.
- `core/` and `application/` are stock-Python domain and use-case layers with no Binary Ninja, Qt, process, or network imports.
- `providers/` owns supervised Claude Code, Codex, and Ollama Cloud adapters; prompts go through stdin and credentials stay with each CLI.
- `host/` owns Binary Ninja context packs, storage location, settings, background work, callbacks, and registration.
- `ui/` owns context preview, evidence navigation, the Qt6 sidebar/settings, transcript, progress, and sanitized Markdown.
- `application/conversations.py` owns bounded local transcript storage; `core/evidence.py` owns citation classification.
- Current boundaries are in `docs/architecture.md`; future phases are in `docs/roadmap.md`.

## Gotchas

- Binary Ninja 5.x hosts Qt6. Do not introduce a PySide2-only import path.
- Stock Python tests cannot import `binaryninja`; `__init__.py` must keep pure modules importable without the host.
- The plugin delegates authentication to installed CLIs and must never read or persist their credentials.
- Raw provider Markdown is untrusted. The transcript must keep importing with
  `QTextDocument.MarkdownNoHTML`; do not escape the source string instead,
  because CommonMark leaves entities undecoded inside fenced code.
- Version 0.9 is read-only and must not mutate the BNDB.
- Extra context packs are opt-in; generic provider links stay inert and transcript persistence stays off by default.
- A real Binary Ninja GUI launch is required to prove sidebar registration.

## Definition of done

- Unit tests, compileall, and plugin metadata validation pass.
- A development install reports no drift and Binary Ninja launches with the sidebar registered.
- Provider prompts remain off process command lines; previews match frozen snapshots; no secrets, transcripts, or machine-local settings are tracked.

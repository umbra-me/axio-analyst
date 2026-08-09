# Axio Analyst repository instructions

## Commands

- Run tests: `python -m unittest discover -s tests`
- Run one test: `python -m unittest tests.test_axio_analyst.TestPromptConstruction.test_prompt_preserves_evidence_addresses`
- Compile Python: `python -m compileall -q __init__.py models.py prompts.py providers.py registration.py rendering.py settings.py settings_page.py sidebar.py task.py tools tests`
- Validate metadata: `python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"`
- Check a development install: `python tools/plugin_dev.py status --plugins-dir <Binary-Ninja-plugins-dir>`
- Install a development copy: `python tools/plugin_dev.py install --plugins-dir <Binary-Ninja-plugins-dir>`
- Build the Windows demo: `cd samples/demo; ./build.ps1`

## Architecture

- Root Python files are the loadable Binary Ninja plugin; `plugin.json` is its distribution metadata.
- `providers.py` owns supervised Claude Code, Codex, and Ollama Cloud processes. Prompts go through stdin and provider logic does not import Binary Ninja.
- `task.py` is the Binary Ninja boundary for address-labelled HLIL, background work, cancellation, and main-thread callbacks.
- `sidebar.py`, `settings_page.py`, and `rendering.py` own the Qt6 UI and sanitized Markdown transcript.
- `settings.py` owns the machine-local `axioAnalyst` Binary Ninja settings namespace.
- The end-state architecture and safety model are in `docs/architecture.md`.

## Gotchas

- Binary Ninja 5.x hosts Qt6. Do not introduce a PySide2-only import path.
- Stock Python tests cannot import `binaryninja`; `__init__.py` must keep pure modules importable without the host.
- The plugin delegates authentication to installed CLIs and must never read or persist their credentials.
- Raw provider Markdown is untrusted. Keep HTML escaping before Qt rendering.
- Version 0.7 is read-only and must not mutate the BNDB.
- A real Binary Ninja GUI launch is required to prove sidebar registration.

## Definition of done

- Unit tests, compileall, and plugin metadata validation pass.
- A development install reports no drift and Binary Ninja launches with the sidebar registered.
- Provider prompts remain off process command lines and no secrets or machine-local settings are tracked.

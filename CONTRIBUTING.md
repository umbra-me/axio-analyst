# Contributing

Axio Analyst is currently developed against Binary Ninja 5.4 and its Qt6 UI.
Contributions should preserve the provider-neutral architecture, testability
outside Binary Ninja, and the current read-only security boundary.

## Before starting

- Read `AGENTS.md` for exact commands and repository constraints.
- Read `docs/architecture.md` for module ownership and roadmap boundaries.
- Check `CHANGELOG.md` and `docs/handoff.md` for current state and blockers.
- Discuss runtime, native, privileged, paid, or credential-management
  dependencies before implementing them.
- Use only binaries and provider output that you are authorized to share.

## Development expectations

- Keep changes focused and match the surrounding Python style.
- Keep provider, parser, prompt, and rendering logic importable under stock
  Python. Do not make their tests depend on a Binary Ninja licence.
- Keep provider work off the GUI thread and Qt updates on the main thread.
- Do not read CLI credential files or persist tokens in settings, logs, tests,
  fixtures, or documentation.
- Preserve raw-HTML escaping and the current-function context cap.
- Add direct tests for provider command construction, output parsing, error
  behavior, cancellation, and streaming changes.
- Update the maintained document that owns changed behavior.

## Verification

Run the complete local suite from the repository root:

```powershell
python -m unittest discover -s tests
python -m compileall -q __init__.py models.py prompts.py providers.py `
  registration.py rendering.py settings.py settings_page.py sidebar.py `
  task.py tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
```

UI changes require the manual checklist in `docs/development.md`. If a real
Binary Ninja launch is unavailable, state that clearly; pure tests are not a
substitute for host validation.

## Commits and pull requests

- Use Conventional Commit subjects such as
  `fix(providers): handle empty result events`.
- Keep implementation, direct tests, and behavior documentation together.
- Explain the user impact, security/data-boundary impact, and verification.
- Do not include generated sample builds, BNDBs, live user settings, provider
  transcripts, credentials, or proprietary binary content.
- Do not bypass failed hooks or checks.

Security-sensitive reports belong through the private process described in
`SECURITY.md`, not a public issue.

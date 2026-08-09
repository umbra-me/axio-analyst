# Axio Analyst

Axio Analyst is a provider-neutral analysis workspace for Binary Ninja. It
sends bounded, address-labelled High Level IL (HLIL) for the function under the
cursor to a supervised Claude Code, Codex, or Ollama Cloud command-line
harness, then streams the response into a native Binary Ninja sidebar.

The current `0.8.0` release is a read-only vertical slice. It is useful for
explaining functions, tracing values, recovering algorithms, and identifying
areas that need deeper investigation. It does not rename symbols, change
types, add comments, or otherwise modify the Binary Ninja database (BNDB).

## Highlights

- Native **Axio Analyst** sidebar with separate Chat and Settings pages.
- **Explain** for a structured current-function summary and **Ask** for custom
  questions (`Ctrl+Enter` submits from the prompt editor).
- Claude Code (`claude -p`), Codex (`codex exec`), and Ollama Cloud
  (`ollama run`) behind one provider-neutral interface.
- Editable model selection and provider-specific reasoning effort.
- Dynamic Ollama Cloud catalog discovery with `ollama list` as an offline
  fallback.
- Streamed, sanitized Markdown responses with stable manual scroll position.
- Background process execution, concurrent stdout/stderr draining, elapsed
  time, phase progress, timeout enforcement, and cancellation.
- Explicit context disclosure and a bounded read-only data boundary.
- Installed version visibility in the sidebar header, Settings page, log, and
  **Plugins > Axio Analyst > About Axio Analyst**.

## Requirements

- Binary Ninja 5.x with its Qt6 UI. Development is currently verified against
  Binary Ninja `5.4.10350-dev`.
- The Python runtime embedded in Binary Ninja; the plugin has no third-party
  Python dependencies beyond Binary Ninja and its bundled PySide6 modules.
- At least one supported provider CLI installed, authenticated, and available
  on `PATH`, or configured by absolute executable path:
  - Claude Code
  - Codex CLI
  - Ollama CLI with Ollama Cloud access

Axio Analyst never reads provider credential files. Authentication remains
owned by the selected CLI.

## Install from source

Binary Ninja loads manually installed Python plugins from a directory under
its user plugin folder. The directory must be named `axio_analyst` and contain
this repository's root `__init__.py`.

Windows PowerShell:

```powershell
git clone https://github.com/umbra-me/axio-analyst.git `
  "$env:APPDATA\Binary Ninja\plugins\axio_analyst"
```

macOS:

```bash
git clone https://github.com/umbra-me/axio-analyst.git \
  "$HOME/Library/Application Support/Binary Ninja/plugins/axio_analyst"
```

Linux:

```bash
git clone https://github.com/umbra-me/axio-analyst.git \
  "$HOME/.binaryninja/plugins/axio_analyst"
```

Restart Binary Ninja after installation or upgrade. Python plugins already
loaded by the current process are not hot-reloaded safely.

For development from a separate checkout, use the bounded copier described in
[Setup and installation](docs/setup.md). It copies only the runtime files and
can report drift without changing the Binary Ninja user directory. Upgrades
from the former flat development layout can use its explicit
`--prune-obsolete` migration flag while Binary Ninja is closed; arbitrary
destination-only files are never removed.

## Versioning

`plugin.json` is the single source of truth for the semantic version. The
runtime validates and reads that value through `core/version.py`; there is no
second hard-coded Python version to synchronize. The installed version appears
in Binary Ninja's plugin metadata, the sidebar header, Settings page, About
command, and registration log.

For a development copy, verify that every manifest-owned installed file and
the metadata version match the checkout:

```powershell
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

## First request

1. Authenticate one supported CLI outside Binary Ninja.
2. Start Binary Ninja and open a binary with analyzed functions.
3. Open **Axio Analyst** from the right sidebar or choose
   **Plugins > Axio Analyst > Open sidebar**.
4. Open **Settings**, select the provider, model, and reasoning effort, verify
   the executable path, and choose **Apply settings**.
5. Place the cursor inside a function.
6. Choose **Explain**, or enter a question and choose **Ask**.

The context card shows the function name, start address, architecture, and the
fact that current-function HLIL is the active context. The provider/model line
shows the persisted configuration that will be used. While a request runs, the
sidebar displays the current phase, elapsed time, streamed output where the
provider supports it, and a **Stop** action.

The plugin also registers these menu commands:

- **Plugins > Axio Analyst > Explain current function**
- **Plugins > Axio Analyst > Ask about current function...**
- **Plugins > Axio Analyst > Open sidebar**
- **Plugins > Axio Analyst > About Axio Analyst**

The Explain and Ask commands use Binary Ninja's plain-text report surface. The
sidebar keeps its own conversation transcript in memory for the lifetime of
that widget.

## Provider behavior

| Provider | Process | Authentication | Streaming behavior |
| --- | --- | --- | --- |
| Claude Code | `claude -p` | Existing CLI OAuth or API-key session | Partial-message text deltas |
| Codex | `codex exec` | Existing CLI OAuth or API-key session | Lifecycle updates and completed agent message |
| Ollama Cloud | `ollama run` | Existing `ollama signin` session | Raw response chunks |

Claude Code runs without tools, Chrome integration, slash commands, or session
persistence. Codex runs ephemerally in a read-only sandbox and ignores user
rules/configuration. Ollama disables prompt history for the child process and
hides thinking output. See [Provider contracts](docs/providers.md) for exact
arguments, parsing rules, limits, and failure behavior.

## What is sent

A request contains only:

- the binary's base filename, not its full path;
- architecture and platform names;
- the selected function's name, start address, and rendered type;
- address-labelled HLIL, truncated to the configured character limit;
- the question and a fixed reverse-engineering instruction.

No request is sent until the user chooses **Ask** or **Explain**. Prompts are
written through stdin rather than included in the process command line.
Provider output is untrusted analysis: confirm important claims against the
cited IL addresses before relying on them.

## Documentation

- [Documentation index](docs/README.md)
- [Setup and installation](docs/setup.md)
- [Configuration reference](docs/configuration.md)
- [Provider contracts](docs/providers.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Development and release guide](docs/development.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Current handoff](docs/handoff.md)
- [Extraction history](docs/history.md)
- [Security policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## Development verification

The provider, prompt, parser, installer, and rendering layers are testable with
stock Python and do not require importing Binary Ninja:

```powershell
python -m unittest discover -s tests -t .
python -m compileall -q __init__.py application core host providers ui tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
```

A real Binary Ninja GUI launch is still required to prove sidebar registration
and Qt behavior because a personal Binary Ninja licence does not expose
`binaryninjaui` to ordinary headless Python.

The harmless C++ reversing fixture lives in [`samples/demo`](samples/demo).
On Windows with CMake and the MSVC toolchain, run:

```powershell
Push-Location samples/demo
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
Pop-Location
```

## Project status

Version `0.8.0` implements the initial read-only vertical slice. Conversation
persistence, richer context packs, direct HTTP providers, credential-store and
OAuth brokerage, structured evidence, reviewable BNDB changes, indexing, and
agent tools remain roadmap work. Current boundaries are documented in
[Architecture](docs/architecture.md), with delivery phases in
[Roadmap](docs/roadmap.md).

Axio Analyst is independently implemented and is not affiliated with or based
on proprietary Binary Ninja Sidekick code, prompts, or data. It is available
under the [MIT License](LICENSE).

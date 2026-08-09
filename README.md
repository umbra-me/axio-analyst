# Axio Analyst

Axio Analyst is a provider-neutral analysis workspace for Binary Ninja. It
builds an inspectable, bounded context snapshot around the function under the
cursor, sends that snapshot to a supervised Claude Code, Codex, or Ollama Cloud
command-line harness, and renders the response in a native Binary Ninja
sidebar.

The current `0.9.0` release remains read-only. It is useful for
explaining functions, tracing values, recovering algorithms, and identifying
areas that need deeper investigation. It does not rename symbols, change
types, add comments, or otherwise modify the Binary Ninja database (BNDB).

## Highlights

- Native **Axio Analyst** sidebar whose resting layout is one header row and one
  composer, with a suggestion-led empty state, a dedicated request-context
  workspace, an original painted mark, and a matching glyph set.
- **Explain** for a structured current-function summary and **Ask** for custom
  questions (`Ctrl+Enter` submits from the prompt editor).
- Exact context preview plus opt-in selection, direct caller/callee, referenced
  string/import, and relevant-type packs under one deterministic total cap.
- Address citations become validated internal navigation targets; unknown
  addresses remain inert and are labelled unresolved.
- Optional, off-by-default local conversation restoration keyed by a path-free
  content fingerprint, with explicit deletion and Markdown export.
- Optional comparison of the active provider with one other configured
  provider using the same frozen context snapshot.
- Per-result latency and character accounting, plus token/cache/cost metadata
  when a provider exposes it.
- Claude Code (`claude -p`), Codex (`codex exec`), and Ollama Cloud
  (`ollama run`) behind one provider-neutral interface.
- Editable model selection and provider-specific reasoning effort.
- Dynamic Ollama Cloud catalog discovery with `ollama list` as an offline
  fallback.
- Streamed Markdown responses with provider HTML disabled at the parser,
  wrapped code blocks, and a stable manual scroll position.
- Background process execution, concurrent stdout/stderr draining, elapsed
  time, phase progress, timeout enforcement, and cancellation.
- Explicit context disclosure and a bounded read-only data boundary.
- Installed version visibility in the sidebar overflow menu, Settings page, log, and
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
in Binary Ninja's plugin metadata, the sidebar overflow menu, Settings page, About
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
6. Choose one of the suggested questions, or type your own and press
   `Ctrl+Enter` (or the send glyph). **Explain this function** is also in the
   header overflow menu once a conversation is under way.

The sidebar header names the current function and its start address. Until the
conversation starts, the space below shows the function, its architecture, the
provider and model that will run, and four suggested questions — so what will
happen is visible before anything is sent.

The composer is one control. The scope chip at its lower left names the request
scope and always shows the pack count: it reads `parse_record` when only the
current function will be sent and `parse_record +N` once N opt-in packs are
enabled, eliding the function name rather than the count when the dock is
narrow. Choosing it opens the dedicated context workspace, where packs are
enabled and **Build preview** inspects the exact snapshot. Every request
rebuilds and freezes that snapshot before provider dispatch, so later cursor
movement cannot silently change it.

The send glyph submits and becomes **Stop** while a request runs. Progress is a
thin line above the composer, and a status line appears beneath it only while
there is something to report — request phase, elapsed time, or the result of an
export, navigation, or restore — then hides itself again. **Explain this
function**, **Compare with**, **Export conversation**, and **Clear
conversation** live in the header's overflow menu, which also reports the
installed version. A completed response opens at its beginning so the first
result is immediately readable.

The plugin also registers these menu commands:

- **Plugins > Axio Analyst > Explain current function**
- **Plugins > Axio Analyst > Ask about current function...**
- **Plugins > Axio Analyst > Open sidebar**
- **Plugins > Axio Analyst > About Axio Analyst**

The Explain and Ask commands use Binary Ninja's plain-text report surface. The
sidebar keeps its conversation in memory by default. Enable **Restore
conversations for this binary** in Settings to store a bounded transcript under
Binary Ninja's user directory. The header's overflow menu holds **Clear
conversation**, which deletes that binary's stored transcript, and **Export
conversation**, which writes the visible conversation as Markdown to a
user-selected path.

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

A request always contains:

- the binary's base filename, not its full path;
- architecture and platform names;
- the primary function's name, start address, rendered type, and
  address-labelled HLIL;
- the question and a fixed reverse-engineering instruction.

When explicitly selected in the Context panel, the same bounded snapshot can
also contain:

- address-labelled HLIL inside the current selection;
- up to three direct callers and five direct callees;
- up to twenty referenced strings and twenty referenced imports;
- relevant function type declarations.

The configured character limit applies to the combined context. Per-function
caps keep one neighbour from consuming the entire request. The exact item list,
content, size, and truncation state are visible before dispatch.

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
- [Sidekick capability inventory](docs/sidekick-capability-inventory.md)
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

The latest live pass used Binary Ninja Personal `5.4.10350-dev` and the demo
fixture. Plugin registration, the resting sidebar, function tracking,
primary/all-pack context previews, Settings summaries, version surfaces, and
the read-only boundary passed without provider dispatch. Provider interaction,
narrow keyboard traversal, persistence, and restart cases remain explicitly
deferred. See the dated [GUI verification report](docs/gui-verification.md).

The harmless C++ reversing fixture lives in [`samples/demo`](samples/demo).
On Windows with CMake and the MSVC toolchain, run:

```powershell
Push-Location samples/demo
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
Pop-Location
```

When launching the fixture through `binaryninja.exe`, pass it as a positional
file argument. Binary Ninja's built-in help defines
`-l, --debug-log <file>` as the log destination; it is not the option for
opening the fixture. The exact safe command and recovery note are in the
[demo guide](samples/demo/README.md).

## Project status

Version `0.9.0` implements the bounded context, evidence navigation, optional
local transcript, provider comparison, and usage-accounting milestone. Direct
HTTP providers, credential-store and OAuth brokerage, reviewable BNDB changes,
indexing, and agent tools remain roadmap work. Current boundaries are
documented in [Architecture](docs/architecture.md), with delivery phases in
[Roadmap](docs/roadmap.md).

Axio Analyst is independently implemented and is not affiliated with or based
on proprietary Binary Ninja Sidekick code, prompts, or data. It is available
under the [MIT License](LICENSE).

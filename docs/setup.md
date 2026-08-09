# Setup and installation

Axio Analyst is currently distributed from source. Binary Ninja discovers it
as a user plugin when a directory named `axio_analyst` containing the root
`__init__.py` is present in the Binary Ninja user plugin folder.

## Prerequisites

1. Binary Ninja 5.x with the Qt6 desktop UI.
2. Git for a source installation, or Python 3.10+ for the development copier.
3. One supported provider CLI:
   - Claude Code (`claude`)
   - Codex CLI (`codex`)
   - Ollama (`ollama`) with Ollama Cloud access
4. An authenticated session established directly with the selected CLI.

Confirm the available CLIs in the same desktop environment that launches
Binary Ninja:

```powershell
claude --version
codex --version
ollama --version
```

Only one provider is required. If Binary Ninja is launched from a desktop
shortcut and cannot see a CLI that works in a terminal, configure its absolute
executable path from the Axio Analyst Settings page.

## Binary Ninja user plugin folders

The standard plugin locations are:

| Platform | User plugin folder |
| --- | --- |
| Windows | `%APPDATA%\Binary Ninja\plugins` |
| macOS | `~/Library/Application Support/Binary Ninja/plugins` |
| Linux | `~/.binaryninja/plugins` |

Binary Ninja's **Open Plugin Folder** command is the safest way to confirm a
non-standard or overridden user directory. `BN_USER_DIRECTORY` can override
the entire Binary Ninja user directory for isolated testing.

## Source installation

Clone directly into an `axio_analyst` child directory.

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

Restart Binary Ninja. Open a binary, place the cursor inside a function, then
use the right sidebar or **Plugins > Axio Analyst > Open sidebar**.

## Development installation

Keep the Git checkout outside the Binary Ninja user directory and copy only the
runtime files:

```powershell
python tools/plugin_dev.py install `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

Preview the exact copies without changing anything:

```powershell
python tools/plugin_dev.py install `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins" `
  --dry-run
```

Check whether the installed runtime matches the checkout:

```powershell
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

The copier manages these files and no others:

```text
__init__.py        models.py          plugin.json
prompts.py         providers.py       registration.py
rendering.py       settings.py        settings_page.py
sidebar.py         task.py
```

It does not delete destination-only files, change Binary Ninja settings, copy
tests or documentation, touch databases or licences, or inspect provider
credentials.

## Provider preparation

Authenticate outside Binary Ninja using the provider's normal CLI flow. Axio
Analyst relies on that existing session and does not expose a sign-in form.

- Claude Code must accept a non-interactive `claude -p` request.
- Codex must accept `codex exec` with JSON output.
- Ollama must be signed in for cloud access, and the chosen model must be a
  runnable cloud tag.

Use the Settings page to choose a model and reasoning effort. The model field
is editable so a newly released or account-specific name can be entered even
when it is not in the built-in suggestions.

## Upgrade

For a direct source installation:

```powershell
Set-Location "$env:APPDATA\Binary Ninja\plugins\axio_analyst"
git pull --ff-only
```

For a separate development checkout, update the checkout and rerun
`tools/plugin_dev.py install`. Restart Binary Ninja after either method.

Before upgrading across a settings-namespace or storage migration, read
`CHANGELOG.md`. Version `0.7.0` stores only user settings under
`axioAnalyst.*`; there is no conversation database to migrate.

## Remove

Close Binary Ninja, then remove only the exact `axio_analyst` plugin directory
from the confirmed user plugin folder. The development copier intentionally has
no uninstall action because deletion must remain explicit.

Removing the plugin directory does not remove `axioAnalyst.*` values from
Binary Ninja's user settings. Those values contain executable paths, model
names, effort choices, and request limits, not provider credentials.

## First-run validation

After restarting Binary Ninja:

1. Confirm **Axio Analyst** appears in the right sidebar and Plugins menu.
2. Open Settings and confirm the configured executable path.
3. Apply a provider, model, and reasoning selection.
4. Select a function with HLIL and send a simple explanation request.
5. Confirm progress appears, output renders as Markdown, and **Stop** is enabled
   during the request.
6. Check the Binary Ninja log if the sidebar or request fails.

Use the C++ fixture in `samples/demo` when a harmless known binary is needed.

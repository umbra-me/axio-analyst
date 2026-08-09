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

A zero exit reports `Axio Analyst is current`. A nonzero exit identifies
missing, changed, or known obsolete runtime paths without modifying them.

The copier manages the root entry point and metadata plus the runtime packages
below:

```text
__init__.py
plugin.json
application/
core/
host/
providers/
ui/
```

`tools/runtime_manifest.py` is the exact per-file allowlist. A contract test
ensures every Python module under those packages is represented before the
copier can be considered complete.

By default, it does not delete destination-only files, change Binary Ninja
settings, copy tests or documentation, touch databases or licences, or inspect
provider credentials.

After upgrading a development copy from the former flat layout, old root
modules are reported as obsolete. While Binary Ninja is closed, remove exactly
those known modules during installation with:

```powershell
python tools/plugin_dev.py install `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins" `
  --prune-obsolete
```

The flag does not recursively clean the plugin directory or remove arbitrary
destination-only files. It is intended specifically for migration from the
tracked flat modules used before `0.8.0`.

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
`tools/plugin_dev.py install`. Add `--prune-obsolete` only when status reports
the known flat-layout modules. Restart Binary Ninja after either method.

Before upgrading across a settings-namespace or storage migration, read
`CHANGELOG.md`. Version `0.9.0` adds the off-by-default
`axioAnalyst.persistConversations` setting and schema-version-1 JSON records
under `<Binary Ninja user directory>/axio-analyst/conversations/`. There is no
automatic migration from another product or location.

## Remove

Close Binary Ninja, then remove only the exact `axio_analyst` plugin directory
from the confirmed user plugin folder. The development copier intentionally has
no uninstall action because deletion must remain explicit.

Removing the plugin directory does not remove `axioAnalyst.*` values from
Binary Ninja's user settings. Those values contain executable paths, model
names, effort choices, request limits, and the persistence preference, not
provider credentials.

If local conversation persistence was enabled, remove its data separately only
after resolving the exact user directory. Prefer opening each binary and using
**Clear**, which deletes only that fingerprint's record. Do not recursively
remove the Binary Ninja user directory; it may contain licences, symbols,
settings, and unrelated plugins.

## First-run validation

After restarting Binary Ninja:

1. Confirm **Axio Analyst** appears in the right sidebar and Plugins menu.
2. Confirm the sidebar header, Settings introduction, About command, and
   registration log show the version from `plugin.json`.
3. Open Settings and confirm the configured executable path.
4. Apply a provider, model, and reasoning selection.
5. Select a function with HLIL, choose **Context**, enable one safe pack,
   confirm the button reports `Context +1`, and confirm **Build preview** shows
   exact bounded text without a full path.
6. Send a simple explanation request and confirm the context summary matches
   the dispatched snapshot.
7. Confirm progress appears, output renders as Markdown, address citations can
   navigate internally, unresolved addresses remain inert, and **Stop** is
   enabled during the request.
8. Optionally choose **Compare with** in the **Ask** menu to add a second
   configured provider, and confirm both labelled outputs show separate usage
   metadata.
9. Enable persistence only for a non-sensitive fixture, restart the sidebar,
   confirm restoration, use the header overflow menu to export Markdown, then
   use **Clear conversation** and confirm the record no longer restores.
10. Check the Binary Ninja log if the sidebar or request fails.

Use the C++ fixture in `samples/demo` when a harmless known binary is needed.

# Binary Ninja GUI verification

This page records the latest real-host verification for Axio Analyst. It
separates checks completed without provider dispatch from checks that require
an explicitly authorized provider or local test harness.

## Latest result

Date: 2026-08-10

- Axio Analyst source and installed version: `0.9.0`
- Binary Ninja: Personal `5.4.10350-dev` on Windows x86_64
- Fixture: `samples/demo/build/Release/axio_analyst_demo.exe`
- Result: the non-network GUI shell passed; provider-dependent interaction
  remains partially verified.

The installed development copy reported current before and after the check.
The Binary Ninja log contained
`Axio Analyst v0.9.0: plugin registration complete.` with no registration
error or Python traceback.

## Completed live checks

| Area | Evidence |
| --- | --- |
| Host load | Binary Ninja recognized the fixture as PE, completed analysis, loaded the plugin, and opened the Axio Analyst sidebar. |
| Resting layout | The split-diamond mark, header, empty state, four suggestions, scope chip, keyboard hint, and send glyph rendered correctly. No status band was visible at rest. |
| Version surfaces | The registration log, Settings introduction, and overflow menu all displayed `0.9.0`. |
| Function tracking | Moving from `main` to `sub_140001000` updated the sidebar name and address and invalidated the old context preview. |
| Primary preview | `main` produced one item and 3,275 characters of address-labelled current-function context. |
| Expanded preview | Enabling callers, callees, referenced strings, referenced imports, and relevant types produced eight items and 14,195 characters. No source path was shown. |
| Settings | Provider/model values rendered, collapsed sections showed staged summaries, and Request limits expanded to the staged 270-second and 65,000-character values. The section was collapsed again without applying a change. |
| Read-only boundary | No provider request was sent, no BNDB was created, no symbol/type/comment change was made, and the repository remained clean. |
| Shutdown | The verification instance started for the check closed cleanly. |

The stock-Python suite also passed 55 tests, `compileall` completed, plugin
metadata parsed, and `plugin_dev.py status` reported the installed runtime
current.

## Deferred live checks

The following items were not claimed as passed in this run:

- narrow-dock keyboard focus traversal and `Ctrl+Enter` submission;
- suggestion dispatch, streaming, progress, elapsed time, cancellation, and
  status auto-hide;
- every configured provider and the two-provider **Compare with** flow;
- answer footers, Markdown edge cases, evidence navigation, and inert links;
- transcript clearing, Markdown export, conversation persistence, and restart;
- applying/reverting every Settings field, live theme switching, inactive mark
  tint, and the About command.

Provider-dependent checks must use only a provider the tester explicitly
authorizes. A local deterministic harness is preferable for rendering,
cancellation, and persistence cases that do not need a real model.

## Fixture launch

Build and run the fixture first:

```powershell
Push-Location samples/demo
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
Pop-Location
```

Then open the generated executable in Binary Ninja. A direct Windows launch can
pass the binary as a positional argument:

```powershell
& "$env:LOCALAPPDATA\Programs\Vector35\BinaryNinja\binaryninja.exe" `
  -n -d .\samples\demo\build\Release\axio_analyst_demo.exe
```

Binary Ninja's built-in command-line help lists `files` as optional positional
arguments and defines `-l, --debug-log <file>` as **Log output to <file>**.
Do not place the fixture immediately after that option; doing so replaces the
generated fixture with log output. If that happens, close only the test
instance and perform the clean rebuild documented in
[`samples/demo/README.md`](../samples/demo/README.md).

## Binary Ninja application updater

During this verification window, Binary Ninja's separate Windows updater
reported **Update Failed: Updater is not valid.** This occurred outside Axio
Analyst. The cached payload's content-addressed hashes matched, and the cached
and installed updater executables were identical and had valid Vector 35
Authenticode signatures. Nothing connected the failure to plugin registration,
runtime files, provider configuration, or the fixture.

Do not remove the Binary Ninja user directory to troubleshoot this message.
Vector 35's [update guide](https://docs.binary.ninja/guide/index.html#updates)
states that Windows updates are applied by a separate launcher and recommends
requesting fresh download links if the self-updater fails. The
[Binary Ninja FAQ](https://binary.ninja/faq/) recommends the customer portal or
license-recovery path for current or eligible historical installers. See
[`troubleshooting.md`](troubleshooting.md#binary-ninja-reports-updater-is-not-valid)
for the safe recovery sequence.

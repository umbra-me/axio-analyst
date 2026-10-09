# Binary Ninja GUI verification

This page indexes dated real-host verification for Axio Analyst. Historical
receipts apply to their recorded source, not automatically to later changes.

## Latest result

The latest recorded real-host checks are from **2026-09-05**, using Binary Ninja
Personal `6.1.10608-dev` on macOS and the bundled Mach-O demo. The
[September 5 receipt](change-set-2026-09-05.md) records an Ollama response with
unverified findings, evidence navigation, settings surviving restart, and
absence of conversation restore while history was Off. Its follow-up records
cancellation **before output** and restoration of that cancelled conversation
after restart, then history returned to Off.

It does not prove provider switching, Claude/Codex/Compare interaction,
mid-stream cancellation, or successful-response persistence. Those remain
deferred, along with narrow keyboard traversal and the other unobserved cases
below. The October 9 Phase 2 source changes have **not** been installed or
verified in the live Binary Ninja GUI. Native Qt transcript unit tests are
separate from host acceptance.

## Candidate manual plan — October 9

The [manual verification plan](manual-verification.md) gives steps, expected
results, and evidence to record for the deferred cases on source commit
`259b81fb9549f2f0767be97b6499b1443386128b`. Use the
[unfilled results template](manual-verification-results-template.md) for separate
provider, cancellation, and restart observations. Preparation of this plan is
not a live test result. No new GUI receipt has been reported for this candidate.

## Earlier non-network shell receipt

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

### Completed live checks on August 10

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

### Deferred at the August 10 checkpoint

The following items were not claimed as passed in that run. Consult the dated
September 5 receipt above for the narrowly completed subset:

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

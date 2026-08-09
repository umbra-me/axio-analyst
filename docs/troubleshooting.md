# Troubleshooting

Start with Binary Ninja's log and the status text in the Axio Analyst sidebar.
The plugin converts expected provider failures into user-visible messages and
logs unexpected registration or callback failures.

## Axio Analyst does not appear

Check the installation shape. The plugin folder must be exactly:

```text
<Binary Ninja user directory>/plugins/axio_analyst/__init__.py
<Binary Ninja user directory>/plugins/axio_analyst/plugin.json
<Binary Ninja user directory>/plugins/axio_analyst/{application,core,host,providers,ui}/
```

A common mistake is an extra directory level such as
`plugins/axio-analyst/axio-analyst/__init__.py`. Use Binary Ninja's
**Open Plugin Folder** command to confirm the active user directory.

Then check:

- Binary Ninja was fully restarted after installation;
- user plugins are not disabled with `-p` or `BN_DISABLE_USER_PLUGINS`;
- the installed runtime matches the checkout with `plugin_dev.py status`;
- Binary Ninja's log has no Python import or Qt registration error;
- the host is Binary Ninja 5.x with PySide6/Qt6.

`plugin_dev.py status` reports three kinds of drift: manifest files that are
missing, manifest files whose content changed, and known obsolete root modules
from the pre-0.8 flat layout. Close Binary Ninja and use `install
--prune-obsolete` only for that explicit legacy-module list. The installer does
not recursively clean the plugin directory or remove unrelated files.

The two function commands are registered before the sidebar import. If the menu
commands exist but the sidebar does not, focus on `binaryninjaui`/PySide6 and
sidebar-registration errors rather than provider configuration.

## Binary Ninja reports Updater is not valid

The **Update Failed: Updater is not valid.** dialog belongs to Binary Ninja's
application updater. It is not emitted by Axio Analyst, its development
installer, or a provider adapter. If Axio Analyst still registers and
`plugin_dev.py status` reports current, diagnose the application update path
separately.

Use this recovery order:

1. Close Binary Ninja normally, confirm no analysis session still needs saving,
   and retry **Help > Check for Updates** once.
2. Confirm the intended stable or development channel in **Update Channel** and
   that Binary Ninja can reach its update service. A proxy can be configured
   through Binary Ninja's HTTPS proxy setting.
3. If the same validation error returns, leave `%APPDATA%\Binary Ninja`
   intact. It contains the licence, settings, user plugins, symbols, and other
   unrelated state.
4. Obtain a fresh eligible installer from the Binary Ninja customer portal or
   licence-recovery path and use it to update/repair the application. Vector
   35 documents this as the fallback when the self-updater fails.
5. If a fresh installer also fails, report the exact Binary Ninja build,
   channel, Windows version, and sanitized error to Vector 35 support.

Do not delete the update cache or reinstall Axio Analyst merely because this
dialog appears. The 2026-08-10 observation recorded in
[`gui-verification.md`](gui-verification.md#binary-ninja-application-updater)
found matching content hashes and valid Vector 35 signatures on both updater
executables, while Axio Analyst continued to load normally. That evidence makes
the plugin an unlikely cause but does not identify the updater's internal
validation failure.

Official references:

- [Binary Ninja updates](https://docs.binary.ninja/guide/index.html#updates)
- [Binary Ninja FAQ](https://binary.ninja/faq/)
- [Binary Ninja support and licence recovery](https://binary.ninja/support/)

## The displayed version is unexpected

The authoritative version is the string in the installed `plugin.json`.
Axio Analyst reads the same value for the sidebar overflow menu, Settings page, About
command, and registration log. If those surfaces disagree with the checkout:

1. Close Binary Ninja so imported Python modules are not reused.
2. Run `plugin_dev.py status` against the confirmed user plugin folder.
3. Reinstall the manifest-owned runtime and confirm status reports current.
4. Restart Binary Ninja and check the registration log again.

An invalid or non-semantic version in `plugin.json` intentionally prevents the
plugin from loading. Correct the metadata in the source checkout rather than
hard-coding a different Python version.

## A provider executable is not found

Binary Ninja may inherit a different `PATH` from the terminal where the CLI was
tested. Open Settings and set the executable field to an absolute path, apply
the change, and retry. Confirm the file is executable by the same user running
Binary Ninja.

An empty executable setting is rejected before launch. A missing executable is
reported with the configured name/path.

## Authentication or account errors

Axio Analyst does not perform login or read credentials. Close the request,
authenticate with the CLI in a normal terminal, confirm a minimal headless
request works there, and retry from Binary Ninja. Do not paste tokens into the
model or executable fields.

Model access is account-dependent. A name shown in a suggestion list or public
catalog does not prove that the current account can run it.

## Ollama Cloud models do not populate

Discovery first fetches Ollama's public catalog, then falls back to
`<configured ollama executable> list`.

Check the Settings status message, then verify:

```powershell
ollama --version
ollama list
```

Possible causes include blocked network access to `ollama.com`, an unavailable
or invalid public response, an executable path visible only in another shell,
an unsigned-in Ollama CLI, or no registered cloud models. The model field stays
editable; enter a known cloud tag manually and apply settings.

## A request times out

The timeout covers the entire provider process. Increase
`axioAnalyst.timeoutSeconds` in Settings only after checking that the CLI is not
waiting for an interactive login, permission prompt, model download, or other
input that the supervised process cannot answer.

Long HLIL and enabled relationship packs can increase latency. Reduce
`maxContextChars`, disable unnecessary packs, or ask about a smaller function.
Every truncated item and the overall context summary are labelled in the exact
preview and prompt.

## A request produces malformed or empty output

Run the same CLI version in a terminal and inspect whether its structured
output format changed. Axio Analyst currently expects:

- Claude Code JSON, event arrays, or JSON Lines with a final result;
- Codex JSON Lines with a completed agent message;
- Ollama text on stdout.

Capture only a sanitized structural sample when filing an issue. Remove
prompts, binary contents, paths, tokens, identifiers, and proprietary output.

## Streaming looks delayed

Axio Analyst coalesces small updates before dispatching them to Qt. Claude Code
usually exposes partial-message deltas, Ollama exposes pipe chunks, and Codex
currently exposes lifecycle events followed by its completed agent message.
These differences are provider behavior, not three identical token streams.

While output streams, the transcript follows the live tail only when it was
already near the bottom. Manually scrolling upward keeps the reading position.
When the request completes, the transcript moves to the beginning of the new
provider response so a long answer does not leave only its final lines visible.

## Stop does not return immediately

Cancellation asks the provider process to terminate and waits up to two
seconds before killing it. A child process or provider wrapper may therefore
take a short time to disappear. The sidebar retains any partial text and marks
the request cancelled.

## Markdown appears unsafe or incorrectly formatted

The transcript imports Markdown with `QTextDocument.MarkdownNoHTML`, so
HTML-looking model output must appear as literal text rather than active
markup. Generic links are not opened by the transcript. Only address anchors
constructed and validated by Axio Analyst may navigate inside Binary Ninja. If
a formatting change bypasses this behavior, stop using that build and report it
as a security issue.

Fenced code blocks wrap instead of scrolling the transcript sideways, and they
render `<`, `>`, and `&` literally. Seeing `&lt;`, `&gt;`, or `&amp;` inside a
code block means the source string is being escaped before the Markdown import
again; CommonMark does not decode entities inside code, so that escaping must
not be reintroduced.

## Context preview is empty or missing expected items

The primary function requires HLIL. Selection context also requires a non-empty
address selection whose HLIL instruction addresses fall inside the selected
range. Caller/callee discovery is direct and bounded; indirect calls or
unresolved targets may produce no item. Strings and imports are derived from
data references emitted by instructions in the primary function, so values
without a resolvable Binary Ninja string/import symbol are omitted.

The configured limit is shared by all items. If a later item is absent, inspect
the character total and truncation marker, then reduce other packs or increase
the limit deliberately. The preview is a snapshot, not a live editor; choose
**Build preview** again after changing the selection or pack checkboxes.

## An address citation does not navigate

Only `0x` hexadecimal citations that Binary Ninja reports as valid offsets are
made clickable. Citations outside the current BinaryView are listed as
unresolved and remain inert. If a valid-looking address does not navigate,
confirm the binary/view has not changed and include the view type and sanitized
address behavior in a report; do not include proprietary surrounding text.

## A conversation does not restore

Persistence is off by default. Enable **Restore conversations for this binary**
and choose **Apply settings** before completing a request. Records are keyed by
a sampled content fingerprint, so materially changed/rebased contents can map
to a different record. Disabling the setting stops loading and saving but does
not delete existing data; re-enable it or use **Clear** while the matching
binary is open.

Malformed, unknown-schema, or oversized records are rejected rather than
partially loaded. The status line reports the local error. Do not hand-edit a
record containing sensitive transcript text for a bug report; reproduce with
the demo binary instead.

## Provider comparison shows one failure

Comparison invokes the primary provider first, then the selected alternative,
using one frozen prompt. A missing executable, unavailable model, auth failure,
or timeout is contained to that provider and displayed beside a successful
result. Verify the failing backend's saved executable/model independently.
Choosing the active backend as the comparison intentionally runs only once.

## Diagnose a plugin-related Binary Ninja startup problem

Binary Ninja can start with user plugins disabled using its `-p` option or the
`BN_DISABLE_USER_PLUGINS` environment variable. Use that only to isolate the
cause, then inspect the user plugin directory and log. Do not delete the entire
user directory: it may contain licences, settings, symbols, and unrelated
plugins.

## Information to include in a report

- Axio Analyst version and commit;
- Binary Ninja version, OS, and architecture;
- provider CLI name and version, without account details;
- whether the failure occurs during startup, discovery, dispatch, streaming,
  parsing, cancellation, or shutdown;
- exact sanitized error text;
- the smallest non-proprietary reproduction, preferably `samples/demo`.

Never include credentials, a populated settings file, private binary content,
or an unsanitized provider transcript.

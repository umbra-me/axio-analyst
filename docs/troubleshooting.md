# Troubleshooting

Start with Binary Ninja's log and the status text in the Axio Analyst sidebar.
The plugin converts expected provider failures into user-visible messages and
logs unexpected registration or callback failures.

## Axio Analyst does not appear

Check the installation shape. The plugin folder must be exactly:

```text
<Binary Ninja user directory>/plugins/axio_analyst/__init__.py
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

The two function commands are registered before the sidebar import. If the menu
commands exist but the sidebar does not, focus on `binaryninjaui`/PySide6 and
sidebar-registration errors rather than provider configuration.

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

Long HLIL can also increase latency. Reduce `maxContextChars` or ask about a
smaller function. A truncated request is labelled in the prompt and transcript
context remains limited to the current function.

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

When the transcript is manually scrolled away from the bottom, new output does
not force it back to the live tail. Scroll near the bottom to resume following.

## Stop does not return immediately

Cancellation asks the provider process to terminate and waits up to two
seconds before killing it. A child process or provider wrapper may therefore
take a short time to disappear. The sidebar retains any partial text and marks
the request cancelled.

## Markdown appears unsafe or incorrectly formatted

Raw provider HTML must remain escaped. HTML-looking model output should appear
as text rather than active markup. Links are not opened by the transcript. If a
formatting change bypasses this behavior, stop using that build and report it
as a security issue.

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

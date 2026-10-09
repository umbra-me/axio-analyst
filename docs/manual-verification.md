# Manual Binary Ninja verification

Prepared: 2026-10-09. Target runtime source commit:
`259b81fb9549f2f0767be97b6499b1443386128b`, version `0.9.0`.

This is a test plan. No case below has a new live result. Record your observations
in [the results template](manual-verification-results-template.md); only dated,
reported observations will be added to [GUI verification](gui-verification.md).
The September receipts and October unit tests do not count as passes here.

## Preparation — G00

1. Finish or save unrelated Binary Ninja work before a full application restart.
   Use only the harmless [demo fixture](../samples/demo/README.md) for provider
   requests. Keep its build unchanged throughout persistence tests.
2. From the repository root, record `git rev-parse HEAD`, `git status --short`,
   and the version in `plugin.json`. Later documentation-only commits are valid
   for this plan if the command below shows no runtime/tool/metadata difference.
   If it shows a runtime change, start a new receipt for that revision and review
   the affected expectations before testing.

   ```sh
   git diff 259b81fb9549f2f0767be97b6499b1443386128b HEAD -- __init__.py plugin.json application core host providers ui tools
   ```
3. Build the fixture if needed. On macOS/Linux:

   ```sh
   (cd samples/demo && ./build.sh && ./build/axio_analyst_demo --demo)
   ```

   On Windows PowerShell:

   ```powershell
   Push-Location samples/demo
   .\build.ps1
   .\build\Release\axio_analyst_demo.exe --demo
   Pop-Location
   ```

4. Record the executable's SHA-256. On macOS use
   `shasum -a 256 samples/demo/build/axio_analyst_demo`; on Linux use `sha256sum`
   with that path; on Windows use
   `Get-FileHash .\samples\demo\build\Release\axio_analyst_demo.exe -Algorithm SHA256`.
5. Fully close Binary Ninja before installing the candidate. Confirm the actual
   plugin folder through Binary Ninja's **Open Plugin Folder** first. From this
   checkout run the appropriate commands below. Substitute the confirmed parent
   plugin directory if it differs; do not use `--prune-obsolete` for this update.

   macOS:

   ```sh
   python3 tools/plugin_dev.py install --plugins-dir "$HOME/Library/Application Support/Binary Ninja/plugins"
   python3 tools/plugin_dev.py status --plugins-dir "$HOME/Library/Application Support/Binary Ninja/plugins"
   ```

   Windows PowerShell:

   ```powershell
   python tools/plugin_dev.py install --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
   python tools/plugin_dev.py status --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
   ```

   Linux:

   ```sh
   python3 tools/plugin_dev.py install --plugins-dir "$HOME/.binaryninja/plugins"
   python3 tools/plugin_dev.py status --plugins-dir "$HOME/.binaryninja/plugins"
   ```

6. Start Binary Ninja Personal normally, open the generated executable, and wait
   for analysis. Open the Axio Analyst sidebar. Record the Binary Ninja build,
   OS/architecture, registration log, overflow-menu version, and Settings version.
7. Record existing provider/model/effort, executable overrides, timeout, context
   limit, and history preference locally so you can restore them. Do not share
   absolute paths or populated settings files. Set Local history **Off**, timeout
   **300 s**, and context limit **60,000** with **Apply** for the initial tests.
8. Choose **No comparison** under the header's **More actions > Compare with**.
   Open the composer's scope chip and disable every optional pack. Choose a
   function with HLIL, preferably `validate_access_code` or `main`, and record
   its displayed name/start address; optimized symbols can differ by platform.
9. Record `claude --version`, `codex --version`, and `ollama --version` for the
   installed CLIs you intend to test. Authenticate through their normal CLI
   flows outside Binary Ninja. Use only models your account can run.

**Expected:** installer status says `Axio Analyst is current`; registration has
no import/sidebar traceback; all version surfaces say `0.9.0`; the fixture is
analyzed and requests are idle. Matching the version alone does not prove that
the candidate's runtime files were installed.

**Record:** date/time/timezone, revision/dirty state, fixture hash, installation
status and source of the log, host build, CLI versions, model/effort choices, and
initial preferences. If installation or authentication fails, mark dependent
cases **blocked** with the actual error.

## Run order and receipt rules

Run G01–G03 first; they need no model inference. Selecting Ollama may fetch its
public catalog. Then run G04–G09 with each provider you explicitly choose to
send the public fixture to. Run G10–G14 in order on the same unchanged fixture.
Finish G15–G18 and restore the original preferences.

Use a unique marker such as `AXIO-G04-CLAUDE-<date>-<run>` in each typed request.
Use **pass**, **fail**, **blocked**, or **not run**. A response that finishes
before you can press Stop does not pass cancellation. No deltas from Codex is
expected for this adapter. Record actual times and amounts; there are no assumed
latency, answer-quality, token, or cost targets.

Codex's [snapshot-only confinement gate](providers.md#codex) is still open.
Use the public fixture only; a successful response does not close that gate.
Keep receipts free of credentials, unrelated binaries, account identifiers, and
private paths. Screenshot/export only the public demo conversation you created.

## G01 — Narrow layout and keyboard traversal

**Steps**

1. Test docks approximately 260, 300, and 520 pixels wide, recording the actual
   measured width or stating that it is an estimate. Keep the idle conversation
   and four suggestions visible; do not clear history you need to retain.
2. Click the prompt, type a harmless draft, then use Tab/Shift+Tab to traverse
   reachable prompt, scope, send, Settings, and More actions controls. Activate
   the scope and More actions using keyboard input; close them with Escape or
   their back control. Record the actual focus order and any inaccessible item.
3. In Request context enable two packs, return to chat, and inspect the scope
   chip. Move between two functions and inspect the header and empty state.
4. Open Settings, expand Executables, Request limits, and Local history, then
   collapse them. Inspect labels and values at each width without applying edits.

**Expected:** controls remain usable, wrapped labels are readable, and the scope
chip retains `+2` even if the function name elides. The keyboard hint intentionally
hides below 300 pixels. Function name/address track the cursor. Idle status hides.
Focus order may differ by OS; unreachable required controls are a failure.

**Record:** widths, focus order, clipping/overflow, `+2` visibility, and screenshots
of the narrow chat and expanded Settings. Ctrl+Enter submission is tested in G04.

## G02 — Settings Apply, Revert, and provider selections

**Steps**

1. With no request active, change Provider, Model, and Reasoning; enter an
   identifiable but unsaved model draft. Change one executable draft and limits
   to 270 s/65,000 chars; toggle Local history. Inspect collapsed summaries.
2. Choose **Revert**. Reopen sections and compare every field with your saved
   baseline. Do not dispatch while invalid executable/model drafts are staged.
3. Select Claude Code with Default (CLI) or your permitted model and effort,
   confirm the correct executable, leave history Off, and choose **Apply**.
4. Repeat Apply for Codex and Ollama Cloud, using a runnable Ollama cloud tag.
   Switch among providers and verify their saved model/effort choices survive.
5. Build a preview, change the context limit to 1,000, and Apply. Reopen Request
   context and verify that the old preview has been invalidated. Restore 60,000
   and the chosen provider with Apply. Save these values for G04.

**Expected:** unsaved summaries reflect staged edits; Revert restores saved
values; Apply reports `Settings saved.` Provider model/effort choices are
independent. Applied settings invalidate the preview. Fields are disabled during
an analysis/preview request and usable again afterward.

**Record:** before/draft/reverted/applied values, provider selection method,
status messages, and whether the old preview disappeared. If a dropdown cannot
be operated, record the failure without editing settings files to bypass it.

## G03 — Primary, opt-in, selection, and truncated previews

**Steps**

1. On the recorded function, turn all extra packs Off, then **Build preview**.
   Copy the public snapshot locally and record item/character totals and flags.
2. Enable only Relevant types and rebuild. Inspect which functions' types appear.
3. Enable Direct callers (3) and Direct callees (5), plus Relevant types. Rebuild;
   compare the neighbour names/addresses in HLIL and types.
4. Select a non-empty instruction/address range in the native view. Enable only
   Current selection and rebuild. Check selection addresses against the native
   range. A selection without matching HLIL is not evidence of correct capture.
5. Enable all packs and rebuild; inspect items, string/import values, labels,
   addresses, sizes, and truncation. Missing unresolved references are permitted.
6. Apply a 1,000-character context cap and rebuild on a function whose rendered
   context exceeds it. Inspect the total and truncation markers. Restore 60,000
   afterward. Change function and pack options and check preview invalidation.

**Expected:** primary is always included; Types alone includes only its type;
enabled neighbour HLIL and types use at most the same three callers/five callees.
The combined item-text total stays within the cap. Truncated/partial searches
are labelled, rather than claimed exhaustive. Full paths are absent. Selection
is filtered to the captured half-open address range. The cap excludes prompt
metadata, instructions, and the question.

**Record:** function/range, options, exact preview, counts, totals, and markers.
If the demo is too small to exercise a traversal ceiling, mark that subcase
not run; the unit test result is separate evidence. Return to primary-only.

## G04 — Provider smoke tests and Ctrl+Enter

Run this case independently for **Claude Code**, **Codex**, and **Ollama Cloud**.

**Steps**

1. Apply that provider's executable/model/effort; choose No comparison. Keep the
   fixture, function, 60,000-character limit, and primary-only context fixed.
2. Build a fresh preview. In the prompt type:

   ```text
   AXIO-G04-<PROVIDER>-<date>-<run>
   Explain this function in three short paragraphs. Cite important facts using
   only addresses supplied in the context. Separate observation from inference
   and say when the supplied context is insufficient.
   ```

3. Press **Ctrl+Enter** while the prompt has focus. On macOS use the Control
   modifier with Return; record if the actual shortcut behaves differently.
4. Observe the transition to Stop, visible phase/elapsed status, response, then
   idle Send. Inspect the automatic request preview and the completed footer.
5. Wait at least eight seconds after completion and inspect status auto-hide.
   Open Settings and verify controls are usable again.

**Expected:** exactly one request is dispatched, and no question text remains in
the composer after submission. Claude normally exposes partial text; Ollama
exposes cleaned chunks; Codex may expose only lifecycle updates and final text.
Completion returns controls to idle and opens the answer at its beginning.
Usage shows duration and available token/cache/cost or character accounting;
unavailable fields are not manufactured. Address-bearing findings are unverified.

**Record for each provider:** CLI/model/effort, marker, whether Ctrl+Enter worked,
phase messages, observed streaming style, terminal status, footer, any traceback,
and screenshot/export. Judge answer accuracy separately against the demo source;
receiving an answer proves neither correctness nor filesystem confinement.

## G05 — Explain and suggestion dispatch

**Steps:** on a disposable demo conversation, select one permitted provider.
Use **More actions > Explain this function** once. On a fresh empty demo
conversation, activate each of the four suggestion buttons in turn, returning
to empty only after exporting any history you need. Each activation is a separate
provider request; mark suggestions you do not run individually.

**Expected:** Explain and each suggestion produce one request for the displayed
function, replace the empty state with a conversation, and return to idle.

**Record:** provider, action/suggestion text, displayed function, request count,
phase/status behavior, and whether the empty state disappeared and later returned.

## G06 — Streaming, scrolling, and primary cancellation

Run with each permitted provider; record streaming and cancellation separately.

**Steps**

1. Ask for a moderately long, cited explanation of the public function. While
   text arrives, scroll up and keep an earlier paragraph in view; wait for more
   output. Return to the bottom and observe tail following. Let this run finish.
2. Start another request. After visible response text arrives, note the time and
   press Stop. If it finishes first, record the attempt as not run and retry
   only if desired. For Codex, pre-output lifecycle cancellation may be the only
   observable case; it cannot substitute for mid-stream partial-text evidence.
3. Verify partial text remains with a cancellation marker, controls return to
   idle, and another short request can finish. Export the cancelled conversation.
4. Optionally watch only the provider child started by this test in Activity
   Monitor/Task Manager. Record its PID before Stop and whether it disappears;
   do not stop unrelated CLI or Binary Ninja processes.

**Expected:** manually scrolled text does not jump on every chunk; bottom view
follows new text; completion opens at the response beginning. Successful Stop
retains actual partial output and ends progress. Cleanup can add two seconds
before kill escalation and two seconds afterward, plus other cleanup overhead.
A single host analysis call cannot be preempted. A live preview over 64,000
characters shows a notice while retaining full raw text for terminal rendering.

**Record:** provider, text observed before Stop, Stop-to-idle time, actual status,
partial text/export, scroll behavior, and any observed child PID/exit. Do not
force a huge paid response to reach the preview ceiling; mark that subcase not
run if ordinary output does not reach it. Child disappearance alone does not
prove Windows Job Object assignment or containment of every descendant.

## G07 — Comparison success, failure, and secondary cancellation

**Steps**

1. Apply saved executable/model/effort choices for both providers. With one fixed
   function/options set, choose the other provider under **More actions > Compare
   with**, then send the G04-style question with a new marker.
2. Observe primary progress/output followed by secondary progress, then separate
   labelled sections and usage. Record the displayed snapshot and finding hash.
3. If both providers are permitted, test these pairings separately:

   | Primary | Comparison |
   | --- | --- |
   | Claude Code | Codex |
   | Codex | Ollama Cloud |
   | Ollama Cloud | Claude Code |

4. For one pair, stage a nonexistent executable for the secondary only, Apply,
   and rerun. Use a name such as `axio-analyst-missing-cli`, first confirming it
   does not resolve in your environment. Restore the correct executable with
   Apply immediately afterward.
5. For one permitted pair, start another run. Wait until the status explicitly
   says the secondary is starting/running after the primary completed, then
   press Stop. If the secondary finishes too quickly, mark this attempt not run.
6. Choose No comparison and verify a subsequent request has only one result.

**Expected:** success displays both provider labels and individual accounting.
Missing secondary executable leaves the completed primary beside the error.
Secondary cancellation retains primary text, findings, and usage, marks the
secondary cancelled, and reports `Comparison cancelled; completed results
retained`. Choosing the active backend as comparison collapses to one request.

**Record:** primary/secondary configurations, sequence of statuses, both terminal
sections/footers, snapshot/hash, failure text, and cancellation timing. GUI
observations of one preview/hash do not independently prove identical stdin
bytes across both children; the frozen-prompt unit test is separate evidence.

## G08 — Markdown, evidence navigation, and inert generic links

**Steps**

1. Choose a mapped address shown in the public preview, and verify that
   `0xffffffffffffffff` is not mapped in this demo. With one permitted provider ask:

   ```text
   AXIO-G08-<date>-<run>
   Output a fenced C block containing: if (a < b && b > 0) { return 1; }
   Then output the raw literal HTML token <b>AXIO_HTML</b> outside the code block.
   Include a citation to <MAPPED_ADDRESS_FROM_PREVIEW> and the invalid address
   0xffffffffffffffff, clearly labelled as a deliberate invalid-citation test.
   Include the ordinary Markdown link [generic test](https://example.com/).
   Do not fetch that URL or any other resource.
   ```

2. Inspect the raw Markdown export as well as the rendered answer. If the
   provider omitted/escaped a requested token, mark its rendering subcase not
   exercised; do not credit the parser for text it never received.
3. Click the valid internal citation and compare the native selected address.
   Inspect the invalid citation/unresolved count. Click the generic link and
   confirm no browser/window opens. Test wrapping in the narrow dock.

**Expected:** final code keeps literal `<`, `>`, and `&` and wraps within the
dock. Raw HTML is inert literal text. Validated internal citations navigate;
invalid addresses and generic links do not. Findings remain unverified.

**Record:** actual raw tokens, screenshots, before/after native address, footer
counts, navigation status, and whether any external app opened. Do not inject
Markdown image paths/URLs in this test; HTML disabling does not prove an image
or resource-loading policy, which remains a separate open gate.

## G09 — Export and cancelled export dialog

**Steps:** with history Off and a completed public response, choose **More
actions > Export conversation...**, then cancel the destination dialog. Repeat
and save to a new local test Markdown filename. Open it in a text editor and
compare the marker, roles, response, accounting, citations, unverified finding
metadata, supplied excerpts, and context hash where present. Repeat once with a
cancelled partial response or comparison record from G06/G07.

**Expected:** cancelling the dialog does not write a file or alter the transcript.
An explicit save writes the visible conversation independently of persistence.
Findings do not assert verified status; excerpts can contain supplied demo text.

**Record:** whether cancel wrote anything, completion/error status, and a sanitized
comparison with the visible transcript. Share the demo export only; record local
destination basename rather than an absolute path.

## G10 — Persistence Off across application restart

**Steps:** Apply history Off. With one permitted provider, finish a response
containing `AXIO-G10-<date>-<run>`. Export it. Fully quit/restart Binary Ninja
normally, reopen the same unchanged fixture and sidebar, and inspect history.

**Expected:** the new G10 conversation is absent while history is Off, and saved
provider/model/effort and limits survive restart. An older record may still exist
on disk; absence in the UI does not prove deletion.

**Record:** before/after history checkbox, marker visibility, provider/settings,
registration log, and screenshots. If a full restart is unsafe for other open
work, mark the restart case blocked rather than substituting a sidebar toggle.

## G11 — Completed-response persistence and restart

**Steps:** first preserve any older demo history you need. Apply history On.
Finish a response containing `AXIO-G11-<date>-<run>` and export it. Fully restart
Binary Ninja and reopen the exact same fixture/sidebar. Inspect both the question
and completed answer, footer, findings, and citations; activate one valid citation.

**Expected:** completed response and marker restore, with unverified findings and
metadata preserved. Restored evidence is checked against the reopened BinaryView
before navigation. Provider settings survive independently of conversation data.

**Record:** fixture hash unchanged, history On, exact marker/answer match,
findings/hash/footer, valid navigation before/after, and restart screenshots.
Do not mark this case passed from restoration of a cancelled-only record.

## G12 — Cancelled-response persistence and restart

**Steps:** keep history On. Start a new marked request and Stop before response
output; fully restart and inspect the marked cancellation record. Separately,
with Claude/Ollama if partial text can be observed, Stop after output and restart
again. Export each receipt before reusing the conversation.

**Expected:** question/cancellation marker restores; actual partial text, if any,
also restores. Progress is idle after reopening. No completed response is invented.

**Record:** provider, marker, whether output existed before Stop, partial text,
terminal status, and exact post-restart content. Pre-output and mid-stream are
separate subcases. Record Codex mid-stream as not run if its adapter offers none.

## G13 — Disable/re-enable history without deletion

**Steps:** with a known saved G11/G12 demo record, turn history Off and Apply.
Restart and reopen the fixture; verify no restore. Without sending a new request
or clearing, turn history On and Apply, restart/reopen again, and inspect the
saved marker. Then return to your intended history preference.

**Expected:** Off prevents restoration; it does not delete the existing record.
Re-enabling and reopening restores that same record when no newer save replaced it.

**Record:** checkbox, markers after each reopen, settings/status, and whether any
intervening request was sent. A changed/rebuilt fixture invalidates this test.

## G14 — Clear deletion and empty-state return

**Steps:** run only on demo history you are willing to delete, after exporting
anything needed. With history On and a known saved marker, choose **More actions
> Clear conversation**. Inspect the empty state, then fully restart/reopen the
unchanged fixture with history still On. Check whether the marker returns.

**Expected:** Clear removes the in-memory transcript and the exact sampled
fingerprint record; suggestions return; the old marker does not restore. This
does not delete provider-side history or unrelated conversation records.

**Record:** marker before/after Clear/restart, history preference, status/error,
and empty-state screenshot. Do not delete the whole conversation directory.
Copies of identical bytes can share a record; sampled identity aliases remain.

## G15 — Frozen request and late callbacks after view changes

**Steps**

1. Start a public-demo request for function A, then move to function B in the
   same BinaryView. Record the new header and the original request's context
   when accessible. Let the request finish; distinguish model assertions from
   direct snapshot evidence.
2. Start a second demo request. While it runs, open/switch to a different harmless
   local binary/view so the sidebar owns a different BinaryView. Do not send the
   second binary to a provider. Wait past the old request's completion/cancel
   window, inspect the new transcript/status, then return to the demo.
3. Build a preview and switch functions/binaries while it is running if timing
   allows. Start a new preview in the replacement view and observe whether an
   old result overwrites it. If the preview is too quick, mark the race not run.
4. Optionally close the test binary/sidebar during an active request, reopen it,
   and check for late text, save errors, or crashes. Record the actual close
   action; simply hiding a dock need not destroy its widget.

**Expected:** cursor changes in one binary do not alter dispatched context.
Binary replacement detaches/cancels old work; old results cannot appear, navigate,
or persist as the replacement binary's conversation. Old previews cannot replace
new ones. Liveness checks prevent destroyed-widget updates.

**Record:** A/B names and addresses, binary/view switch, actual statuses and
timestamps, replacement transcript/preview screenshots, errors, and any restored
wrong-binary text. Identical-byte copies are not distinct identity test fixtures.
GUI observations cannot prove that no hidden filesystem write occurred; report
the directly observed result and keep source tests separate.

## G16 — Error recovery and optional live timeout

**Steps:** record the valid executable, then Apply a confirmed nonexistent
executable for one provider. Send a marked demo request; record the error, idle
controls, and whether the UI remains responsive. Restore the correct executable
with Apply and complete a short request. Repeat for each provider if desired.
For an optional timeout attempt, Apply 10 s and start a legitimate demo request;
if it completes inside 10 s, the timeout subcase was not exercised. Restore 300 s
or your original value afterward. Do not induce hangs in an unrelated process.

**Expected:** executable failure is visible and recoverable; no stuck Stop state.
If a real request exceeds its deadline, it fails with timeout, retains any partial
text, and cleans up the test child subject to the documented platform limits.

**Record:** provider, sanitized error, actual duration, request/child state, partial
output, restored settings, and successful retry. No naturally occurring timeout
means no live timeout pass. Deterministic blocked-stdin/post-EOF tests already
exist in the regression suite and are not new manual observations.

## G17 — Ollama discovery and executable supersession

**Steps:** select Ollama Cloud and Refresh without sending inference. Observe
status, model choices, and UI responsiveness; type a permitted manual model tag.
While discovery is active, apply a different executable path if you have another
valid Ollama installation, then record whether results remain consistent with
the applied configuration. If no second path or timing window exists, mark the
supersession subcase not run. Close/destroy the test sidebar during discovery
if practical, then reopen and inspect for errors. Restore the original executable.

**Expected:** discovery does not block Qt; the model stays editable while only
discovery is active; manual selection is preserved. Refresh is disabled during
discovery. Stale results cannot update a superseding request/destroyed sidebar.
The public catalog has a 10 s network timeout/1 MB response cap; local fallback
has a 10 s deadline/1 MB output cap.

**Record:** actual status sequence, chosen model, UI responsiveness, which source
(catalog/list) was visibly used, and any close/supersession issue. Public catalog
success does not exercise `ollama list`; mark fallback not run if not observed.
Do not disable machine-wide networking or install another CLI just for this case.

## G18 — Theme, About, restart, and read-only observations

**Steps:** record the current Binary Ninja theme. Change to one other available
theme through the host UI; inspect chat, context, expanded Settings, code block,
and the active/inactive sidebar mark. Restore the original theme. Use **Plugins
> Axio Analyst > About Axio Analyst**, then compare its version with Settings,
overflow, `plugin.json`, and the registration log. After the restart cases,
compare function names, types, comments, native addresses, and any save/modified
indicators with the baseline. Close only the test work normally.

**Expected:** colors remain readable, mark tints follow activation/theme, and all
version surfaces agree. No plugin-originated symbol/type/comment/BNDB changes
are visible; ordinary host analysis state is recorded separately.

**Record:** theme names, screenshots, About/version text, observed changes/save
prompts, and clean shutdown/errors. A visual inspection is not a complete audit
of database writes. Restore original provider/model/effort/executable/limit/history
preferences through Apply and record the final state.

## Returning results

Fill in [the results template](manual-verification-results-template.md). Start
with G00, G01, G04 per provider, and G10/G11 if you want a smaller first run;
leave all other cases explicitly not run. For every pass include the steps
actually executed and direct evidence. Split partial cases, provider variants,
and distinct restart/cancellation stages instead of combining them into one pass.

Report failed or blocked cases with the actual sanitized error and last action.
Do not label an automation input failure as proof of a plugin defect. Later doc
updates will date only your reported observations and retain all untested gates.

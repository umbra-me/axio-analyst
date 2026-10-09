# Development and release guide

## Repository layout

The repository root is the importable Binary Ninja plugin package, but only
`__init__.py` contains runtime Python at that level. Implementation lives in
packages grouped by dependency boundary.

| Path | Responsibility |
| --- | --- |
| `__init__.py` | Host-aware entry point; does not import Binary Ninja during stock-Python tests. |
| `core/` | Serializable models, provider contract, prompts, and deterministic safety policies. |
| `application/` | Provider-neutral use cases operating on injected interfaces. |
| `providers/` | CLI supervision, streaming, provider adapters, catalog parsing, and factory. |
| `host/` | Binary Ninja context, settings, background tasks, model discovery, and registration. |
| `ui/` | Qt6 sidebar controller/view, settings page, transcript, progress, and Markdown safety. |
| `tests/unit/` | Pure, host-fake, and optional bundled-Qt unit tests arranged by runtime package. |
| `tests/integration/` | Shared process-supervisor tests using harmless local child programs. |
| `tests/contract/` | Repository layout, dependency-boundary, metadata, and installer contracts. |
| `tools/runtime_manifest.py` | Authoritative explicit allowlist of installed runtime files. |
| `tools/plugin_dev.py` | Bounded runtime copier and drift checker. |
| `samples/demo/` | Harmless C++ reverse-engineering fixture; `build.ps1` on Windows, `build.sh` on macOS and Linux. |
| `docs/` | Maintained product, architecture, operations, and handoff documentation. |

## Design constraints

- Supported Binary Ninja hosts use Qt6. Use their bundled PySide6 modules;
  do not add a PySide2-only path.
- Keep `core/`, `application/`, and `providers/` importable without Binary
  Ninja so provider logic remains testable on stock Python. `core/` and
  `application/` must also remain free of Qt, subprocess, and network imports.
- Run provider work in `BackgroundTaskThread` and pipe readers. Return UI
  updates through `execute_on_main_thread`.
- Treat provider Markdown as untrusted and keep importing it with
  `QTextDocument.MarkdownNoHTML` rather than escaping the source string.
- Do not add provider credential access. Harness adapters delegate auth to the
  installed CLI.
- Preserve the read-only boundary introduced in `0.7.0`. Any future BNDB
  writes require a separate preview, validation, transaction, and undo design.
- Do not add runtime, native, privileged, or paid dependencies without an
  explicit distribution decision.

## Local verification

Run from the repository root:

```powershell
python -m unittest discover -s tests -t .
python -m compileall -q __init__.py application core host providers ui tools tests
python -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
```

Run a focused test:

```powershell
python -m unittest `
  tests.unit.core.test_prompts.TestPromptConstruction.test_prompt_preserves_evidence_addresses
```

Optional native Qt transcript tests use Binary Ninja's existing PySide6 bundle;
they do not launch Binary Ninja or dispatch providers. On macOS, from the
repository root with the app at its usual path:

```sh
AXIO_QT_TESTS=1 PYTHONPATH="/Applications/Binary Ninja.app/Contents/Resources/python3" \
  python3 -m unittest tests.unit.ui.test_transcript_qt
```

Use a compatible Python and the actual bundled Python directory on other
systems. Without `AXIO_QT_TESTS=1`, those tests are skipped so the normal suite
remains runnable without Qt. The tested macOS Qt bundle provides the Cocoa
platform plugin, not `offscreen`; these widgets are unshown on the normal
desktop platform.

Check or install the live development copy:

```powershell
python tools/plugin_dev.py status `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
python tools/plugin_dev.py install `
  --plugins-dir "$env:APPDATA\Binary Ninja\plugins"
```

Build the sample on Windows:

```powershell
Push-Location samples/demo
.\build.ps1
.\build\Release\axio_analyst_demo.exe --demo
Pop-Location
```

## Test coverage

The current suite covers:

- required repository/runtime files and plugin metadata;
- address preservation, default questions, and deterministic truncation;
- context ordering, deduplication, combined budgeting, exact rendering, and
  evidence-address classification;
- schema validation, bounded atomic conversation round trips, deletion,
  traversal rejection, and Markdown export;
- provider-neutral duration/character accounting and usage presentation;
- Claude Code, Codex, and Ollama command construction;
- supported Claude event-document/array/JSONL shapes;
- Codex event parsing, final-message extraction, and token/cache usage;
- Claude token/cache/cost/duration usage extraction;
- Ollama local/cloud catalog parsing and cloud-tag normalization;
- executable validation, nonzero exits, timeout, cancellation, output limits,
  concurrent stdout/stderr draining, and streamed chunk delivery;
- blocked-stdin and post-EOF deadlines/cancellation, callback-exception cleanup,
  POSIX descendant cleanup, bounded producer output, split UTF-8, and unique
  temporary-directory cleanup;
- Codex message-before-failure and missing-terminal-event rejection;
- lazy context formatting, late selections, cancellation during collection,
  bounded empty/nonmatching searches, pre-decode value slicing, traversal
  truncation notices, and the same deduplicated neighbour limits in the type pack;
- binary/generation-bound request callbacks and preview invalidation, original
  binary persistence/address validation, and comparison cancellation retaining
  completed primary findings/usage;
- asynchronous Ollama fallback deadline, output cap, close cancellation, and
  stale-result rejection after executable changes;
- optional native Qt incremental text insertion, HTML-disabled final Markdown,
  Unicode/footer placement, completion, failure, cancellation, and reset;
- an 8 MB chunk stream retaining an exact snapshot with a bounded live preview;
- control-character sanitization, code-punctuation preservation, and transcript
  scroll restoration;
- the painted sidebar mark and the HTML-free Markdown import contract;
- injected application orchestration without a concrete provider dependency;
- runtime-manifest completeness and core/application dependency boundaries;
- semantic-version validation and all intended Binary Ninja version surfaces;
- development installer target naming, nested-file copy, drift reporting, and
  exact obsolete-module pruning without deleting unrelated files.

Host-fake and optional native Qt tests exercise source methods without proving
`binaryninjaui` integration, real signal wiring, or host startup. Windows Job
Object cleanup also requires Windows validation. Manual GUI verification is
required before a release.

The [October 9 change set](change-set-2026-10-09.md) records the current local
source verification. Keep its results separate from the historical real-host
receipts in [GUI verification](gui-verification.md).

## Manual GUI checklist

Use [the detailed manual plan](manual-verification.md) for executable steps and
receipt fields for the current candidate. The summary below is the recurring
release checklist; it is not a record of completed observations.

1. Start a supported Binary Ninja build with user plugins enabled.
2. Confirm the log contains the versioned Axio Analyst registration message and
   no import or registration error.
3. Confirm the sidebar rail shows the split-diamond Axio Analyst mark in both
   its active and inactive tints, that it opens the **Axio Analyst** widget,
   and that the overflow menu reports the same version as `plugin.json`.
4. Move between functions and confirm the header and empty state follow the
   cursor and invalidate the old preview.
5. Verify keyboard navigation at narrow sidebar widths: tab from the header
   glyphs through the transcript, prompt, scope chip, and send; confirm
   `Ctrl+Enter` submits and the overflow menu is reachable.
6. Confirm the empty state lists the function, its architecture, and the
   configured provider, and that each suggested question dispatches a request
   and is replaced by the conversation.
7. Confirm the status line stays hidden at rest, appears during a request and
   after an export or evidence navigation, then hides itself again.
8. Drag the dock below and above 300 px. Confirm the scope chip elides the
   function name but never the enabled-pack count, and that Settings switches
   between inline and stacked form rows without clipping wrapped text.
9. Expand and collapse each Settings section and confirm its collapsed summary
   matches the staged values.
10. Apply and revert provider, model, effort, executable, timeout, and context
   settings.
11. Build primary-only and all-pack previews on the demo binary. Confirm exact
   item text, counts, truncation, selection capture, and absence of source paths.
12. Send one request through every provider available to the tester, then use
   the overflow menu's **Compare with** to run a two-provider comparison and
   confirm one frozen context plus separate usage.
13. Confirm streaming behavior, manual-scroll preservation, progress, elapsed
   time, cancellation, contained comparison errors, and transcript clearing.
14. Confirm a fenced code block wraps instead of scrolling the transcript
   sideways and renders literal `<`, `>`, and `&`, while a provider HTML tag
   appears as inert text rather than formatting.
15. Confirm each answer carries one footer line holding its evidence links,
   unresolved-citation count, and usage.
16. Confirm valid evidence addresses navigate, invalid citations remain inert,
   and generic provider Markdown links do not open.
17. Enable persistence for the demo, restart/reopen the sidebar, verify restore
   and Markdown export from the overflow menu, then Clear and verify the exact
   record is deleted and the suggestion empty state returns.
18. Confirm the Settings introduction, overflow menu, and About command display
   the same version.
19. Restart Binary Ninja and confirm persisted settings survive.
20. Confirm no symbol, type, comment, analysis, or BNDB state changed.

The latest real-host receipt is September 5, indexed in
[`gui-verification.md`](gui-verification.md). It records a limited Ollama flow,
evidence navigation, pre-output cancellation and cancelled-history restoration.
It does not establish acceptance of the October 9 patch, other providers,
comparison, mid-stream cancellation, successful-response persistence, or narrow
keyboard traversal.

When launching the fixture from a command line, pass the executable as a
positional argument. Binary Ninja's built-in command-line help lists files
under **Arguments** and defines `-l, --debug-log <file>` as **Log output to
<file>**. It is not the load-file switch.

## Change workflow

1. Read `AGENTS.md` and the documentation owning the behavior being changed.
2. Inspect the working tree and preserve unrelated changes.
3. Keep provider/prompt/parser changes independent of Binary Ninja imports.
4. Add or update direct tests with the implementation.
5. Update README, reference docs, changelog, and handoff when their claims
   change.
6. Run the complete verification commands and manual GUI checks available in
   the environment.
7. Review the staged diff for secrets, generated binaries, user settings, and
   proprietary analysis material.
8. Use Conventional Commit subjects and do not bypass hooks or failed checks.

## Release checklist

The current [release preparation](release-preparation.md) records the selected
version choice, draft notes, open gates and exact future tag/push commands.
It does not authorize or establish publication.

1. Decide the semantic version and update `plugin.json`, the single runtime
   version source.
2. Move relevant `CHANGELOG.md` entries from Unreleased to a dated version.
3. Confirm `README.md`, provider contracts, settings reference, roadmap, and
   handoff describe the shipped behavior.
4. Run the test, compile, metadata, installer, sample, and manual GUI checks.
5. Confirm the sidebar, Settings page, About command, and registration log all
   read the version through `core/version.py`.
6. Confirm the runtime file list in `tools/runtime_manifest.py` is complete.
7. Verify the repository contains no secrets, populated environment files,
   generated sample builds, provider transcripts, or BNDB files.
8. Tag the verified commit only after the release mechanism and Binary Ninja
   plugin-manager metadata have been decided.

There is currently no hosted CI or automated release workflow. Local
verification and a real Binary Ninja launch are the release gates.

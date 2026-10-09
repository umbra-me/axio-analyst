# October 9 change set

## Release-readiness source fixes

The source audit baseline was `9945d84530025139958aad55226c170a18f430f3`.
Implementation, regression tests, and documentation now include the following
fixes. Source version remains `0.9.0`; all changes belong under Unreleased.
This is the source-fix phase of a release-readiness review, separate from the
future product phases in [roadmap.md](roadmap.md).

- The CLI supervisor uses independent stdin/stdout/stderr threads, a 64-chunk
  queue, reader-side combined-output counting, and checks cancellation/deadline
  through process exit. Blocked stdin and post-EOF waits no longer suspend those
  checks. Each run uses a unique temporary directory and attempts tree cleanup
  on success and all failure paths, including callback and cleanup exceptions.
- POSIX cleanup targets a new session/process group. Windows uses a kill-on-close
  Job Object through standard-library `ctypes`; no dependency was installed.
- Codex explicitly disables shell/image tools and web search. Final agent text
  is accepted only with `turn.completed` and no `error`/`turn.failed` event.
- Request and preview callbacks capture a generation and BinaryView identity.
  Binary replacement detaches/cancels old work before loading the replacement
  transcript. Settings invalidate previews; stale callbacks cannot save or
  navigate against the replacement binary.
- Streaming keeps raw chunks and incrementally inserts sanitized literal text
  up to 64,000 live characters. A visible notice discloses that ceiling; full
  raw text remains available for snapshots and the terminal Markdown render.
- Context extraction lazily renders budget-sized HLIL prefixes. Each HLIL pass
  visits at most 100,000 instructions; each neighbour search/reference pack has
  a 4,096-step traversal budget. Exhaustion and partial values are disclosed.
  Values are sliced before decoding/NUL stripping. Neighbour HLIL and type
  packs share the same deduplicated three-caller/five-callee lists.
- Local `ollama list` discovery uses the shared supervisor with a 10-second
  deadline and 1 MB output cap. Executable changes supersede prior discovery;
  stale catalog/list results are discarded.
- Secondary comparison cancellation preserves completed primary text, findings,
  and usage. Cancelling the primary retains its normal partial-text behavior.

Maintained references now describe these contracts and distinguish historical
GUI observations from current source verification. Runtime installation remains
an explicit allowlist; `providers/process_tree.py` is included in it.

## Completed local verification

On October 9, using stock Python 3.14.7 on macOS:

- The stock-Python suite discovered 130 tests: 121 passed and nine optional
  native Qt tests were skipped.
- The full suite using Binary Ninja's existing PySide6/Qt 6.11.1 Cocoa bundle
  passed all 130 tests with no skips. Widgets were unshown; Binary Ninja was
  not launched.
- Compileall, metadata JSON validation, runtime-manifest/dependency/installer
  contracts, diff whitespace, and relative documentation file links passed.

Commands, run from the repository root:

```sh
python3 -m unittest discover -s tests -t .
AXIO_QT_TESTS=1 PYTHONPATH="/Applications/Binary Ninja.app/Contents/Resources/python3" \
  python3 -m unittest discover -s tests -t .
python3 -m compileall -q __init__.py application core host providers ui tools tests
python3 -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
git diff --check
```

Harmless local child programs exercise blocked stdin, closed-output hangs,
output flooding, UTF-8 boundaries, callback failures, cancellation, and POSIX
descendant cleanup. Host fakes cover extraction bounds, callback ownership,
discovery supersession, and comparison cancellation. Native Qt tests cover
literal streaming, Unicode/footer positions, retained partial text, HTML-free
terminal rendering, and exact snapshots of a near-output-limit chunk stream.
These are regression checks, not a latency benchmark or real-host acceptance.

## Remaining gates

- **Codex snapshot-only confidentiality remains unproven.** Read-only execution
  and disabled shell/image/web tools do not establish global tool-off behavior
  or isolation from unrelated readable files. The inspected CLI was `0.153.2`;
  see [the exact provider contract and source reference](providers.md#codex).
- Windows Job Object behavior has not been exercised. Attachment occurs after
  launch; descendants created earlier are not proven contained. POSIX descendants
  can deliberately escape their group, and OS cleanup failures remain possible.
  This is lifecycle supervision, rather than a security sandbox.
- Python cannot preempt a blocked OS process-creation call or a single Binary
  Ninja analysis/property call. Context budgets apply to item text, excluding
  prompt instructions, metadata, and the question.
- HTML disabling is not a validated Markdown image/resource-loading policy.
- Sampled conversation identities can alias binaries that differ only outside
  sampled regions. The existing format is retained; see
  [storage limits](configuration.md#storage-and-secret-handling).
- The updated plugin has not been installed or accepted in the live Binary
  Ninja GUI. Windows behavior, real signal wiring, provider switching/Compare,
  mid-stream cancellation, and successful-response persistence need observed
  receipts. The latest live receipt is still
  [September 5](gui-verification.md#latest-result).

No provider inference, live plugin installation, version bump, tag, push,
release, community submission, or malware walkthrough was performed for this
source checkpoint. The next release-readiness phase is the manual verification
checklist and observed receipts, with installation/provider dispatch authorized
separately. Publication requires its own explicit authorization.

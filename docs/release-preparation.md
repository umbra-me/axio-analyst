# Release preparation

## Source publication update — 2026-10-14

The owner authorized publication of the four preparation commits on `main`,
through `da0b34d98fdb290b27e512e122e3de88b6af687f`; the remote head was
verified. Earlier local/unpushed descriptions below are historical. This is
source publication only: no release tag, host installation, community submission
or workspace pin promotion was performed. Binary Ninja GUI registration,
minimum-host/platform compatibility and the provider/rendering acceptance gates
remain open; follow the existing release checklist before tagging a release.

Prepared October 10, 2026 for release-readiness Phase 5. This page owns the
version decision, release draft, pending gates, and future tag/push commands.
It is not a release receipt.

## Version decision

**Selected `0.9.1` with the maintainer on October 10.** The changelog already has a
dated `0.9.0` entry. A new version distinguishes the lifecycle, callback,
parser, context and rendering fixes, as well as the findings/schema-2 and
presentation changes, from that earlier source. Retaining `0.9.0` would make
those different implementations report the same version.

Source metadata is now `0.9.1`. The
[GitHub release notes](release-notes-draft.md) use selected `0.9.1` for review.
No release date or tag has been assigned. Local tags were inspected on October
10 and the list was empty; remote tags were not checked.

`plugin.json` and current-version guidance are aligned, preserving historical
receipts. The candidate changelog has a `0.9.1 - pending release` entry; assign
the actual release date only when the candidate is accepted for release. The
existing August 10 `0.9.0` entry is intact. `core/version.py` reads metadata;
the runtime does not need a separate hard-coded version edit.

## Evidence and remaining work

The October 9 source fixes are in
`259b81fb9549f2f0767be97b6499b1443386128b`; the manual test plan is in
`f1bf076ed34ec720bcddfaac95cd842a0777a134`. Presentation and release preparation
follow those commits. Record the final candidate's full commit, metadata
version and installed-file hashes before running its live checks.

| Gate | Current evidence / required next step |
| --- | --- |
| Source regression checks | October 10 after the Phase 6 metadata contract: 122 stock-Python passes, nine optional Qt skips; compileall, metadata/runtime version, license parity, 142 relative file links, whitespace and future command syntax passed. October 9 separate bundled-Qt run: 130 passes. Rerun relevant checks if the candidate changes. |
| Live install and host acceptance | No October candidate receipt. Run [G00–G18](manual-verification.md), record exact installed/source identity, and reconcile only reported observations into [GUI verification](gui-verification.md). |
| Codex confidentiality | Open: read-only and shell/image/web flags do not prove snapshot-only isolation. Resolve the documented [provider gate](providers.md#codex) before claiming that boundary. |
| Windows cleanup and supported platforms | Windows Job Object behavior is untested. Establish the supported-platform evidence and record limitations. |
| Markdown resources | HTML is disabled; image/resource-loading policy remains unvalidated. Resolve or explicitly scope this gate before acceptance. |
| Community plugin packaging | [Phase 6 audit](community-submission-audit.md): metadata validator and isolated 36-file layout pass. Minimum-build/platform acceptance remain open before publication; actual manager installation needs a separate distribution receipt. Submission is an unsent draft. |
| Presentation assets | [Real capture plan](capture-plan.md) prepared; no screenshots/GIF produced. |
| Publication authority | No tag, push, release or external submission authorized for execution. Show the final diff/draft and obtain the explicit yes required by the task. |

The broader documented limits (sampled identities, escaped descendants,
individual blocking host/OS calls and provider retention) must stay visible.
No test result here establishes provider performance, accuracy or a benchmark.

## Future verification commands

Run from the repository root on the accepted candidate, using `python3` on
macOS. These commands do not install the plugin or invoke a provider:

```sh
python3 -m unittest discover -s tests -t .
python3 -m compileall -q __init__.py application core host providers ui tools tests
python3 -c "import json,pathlib; json.loads(pathlib.Path('plugin.json').read_text(encoding='utf-8'))"
git diff --check
```

Use [development.md](development.md#local-verification) for optional bundled-Qt
checks and [manual-verification.md](manual-verification.md) for host installation
and live receipts. Stock test skips must be recorded, not silently counted as
passes. No new GUI result should be inferred from these commands.

## Exact future tag and push commands — do not run yet

The following is a macOS/zsh-compatible subshell. It deliberately requires a
full verified commit in place of the placeholder. Use it only after the
final clean local commit, completed release-gate review, resolution of Phase 6
prepublication compatibility gates, and the user's explicit yes to tag and push.
Actual manager installation is a later distribution check. This preparation
does not satisfy those conditions.

These commands fetch remote state, reject an existing tag, require `main` at
the reviewed commit with matching metadata, and reject divergence. Inspect the
listed unpublished commits and diff before authorizing the writes: pushing the
candidate also publishes its unpushed ancestors. The command block does not
create a GitHub release; use the saved notes only after release approval.

```sh
(
  set -eu
  cd /Users/kian/Developer/work/umbra/brands/axio/repos/axio-analyst
  analyst_release_version='0.9.1'
  analyst_release_tag="v$analyst_release_version"
  analyst_release_commit='REPLACE_WITH_VERIFIED_40_HEX_COMMIT'

  python3 - "$analyst_release_commit" "$analyst_release_version" <<'PY'
import json, pathlib, re, subprocess, sys
commit, version = sys.argv[1:]
assert re.fullmatch(r"[0-9a-f]{40}", commit), "Set the verified full commit first"
assert json.loads(pathlib.Path("plugin.json").read_text())["version"] == version
remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
assert remote in {
    "git@github.com:umbra-me/axio-analyst.git",
    "https://github.com/umbra-me/axio-analyst.git",
    "https://github.com/umbra-me/axio-analyst",
}, "Review origin: expected umbra-me/axio-analyst"
PY

  test "$(git branch --show-current)" = 'main'
  test "$(git rev-parse HEAD)" = "$analyst_release_commit"
  test -z "$(git status --porcelain)"
  git fetch origin main
  git merge-base --is-ancestor origin/main "$analyst_release_commit"
  git log --oneline "origin/main..$analyst_release_commit"
  git diff --stat "origin/main..$analyst_release_commit"

  if git show-ref --verify --quiet "refs/tags/$analyst_release_tag"; then
    printf '%s\n' 'Local release tag already exists; stop and inspect.' >&2
    exit 1
  fi
  if git ls-remote --exit-code --refs origin "refs/tags/$analyst_release_tag" >/dev/null; then
    printf '%s\n' 'Remote release tag already exists; stop and inspect.' >&2
    exit 1
  else
    analyst_remote_tag_status=$?
    test "$analyst_remote_tag_status" -eq 2
  fi

  git tag -a "$analyst_release_tag" "$analyst_release_commit" \
    -m "Axio Analyst $analyst_release_version"
  git push origin "$analyst_release_commit:refs/heads/main"
  git push origin "refs/tags/$analyst_release_tag:refs/tags/$analyst_release_tag"
)
```

After pushing, verify that the remote branch and peeled annotated tag both
resolve to the reviewed commit. If either push fails, inspect the actual
local/remote state before retrying; do not force-push or recreate an existing
tag. A Git tag or branch push alone is not a published GitHub release or a
community plugin-manager submission.

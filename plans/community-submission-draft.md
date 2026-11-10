# Community extension issue draft

Prepared October 10, 2026. **Do not send yet:** release URL, final commit and
compatibility receipts are missing. The
[requirements audit](community-submission-audit.md) records what passed and what
remains open. The current [Vector 35 guide](https://docs.binary.ninja/dev/plugins.html)
describes a release followed by an issue; the old index is deprecated, so confirm
the modern catalog route with maintainers before sending. No issue or PR exists.

Proposed issue title: `chore(extensions): submit axio analyst 0.9.1`

## Draft body

Please consider Axio Analyst for the community Extensions catalog.

- Repository: https://github.com/umbra-me/axio-analyst
- Version: `0.9.1`
- GitHub release: **[fill after approved publication]**
- Immutable release commit: **[fill the verified full commit]**
- Maintainer: Kian (Zenco), https://github.com/notzenco
- License: MIT
- Categories/API: UI/helper, Python 3
- Platform metadata: Darwin, Linux, Windows; **[fill actual acceptance matrix]**
- Minimum-build metadata: `4911`; **[resolve the tested support floor]**

Axio Analyst provides a read-only investigation workspace in Binary Ninja.
Users preview bounded, address-labelled function context, explicitly add optional
packs, and ask Claude Code, Codex or Ollama Cloud to explain or compare it.
Address citations are validated for internal navigation; provider conclusions
remain unverified. Local conversation history is opt-in.

The plugin passes the reviewed Vector 35 metadata validator. Its root entry
point and first-level packages are present, MIT metadata matches LICENSE, and
the isolated development copier matches all 36 runtime files. No pip dependency
is required; Qt comes from the host and provider authentication stays with
externally installed CLIs.

Acceptance receipts: **[fill dated host/platform/CLI observations, including
manager installation and restart; do not replace these with source-test counts]**.
Source checks: **[fill final candidate's test/compile/metadata results]**.

Known boundaries are documented in the security policy and provider contracts:
Codex snapshot-only confidentiality is unproven, HTML disabling does not prove
a Markdown resource policy, and process cleanup is not a security sandbox.
**[Resolve or explicitly disposition each release gate before submission; retain
the resulting limits here.]**

The screenshots/GIF are **[pending real capture, or insert the actual URLs]**.
No provider accuracy, speed benchmark, user-count or popularity claim is made.

The legacy community index points to the modern Extensions catalog. Please
confirm this issue is the appropriate onboarding route, or direct me to the
current submission channel.

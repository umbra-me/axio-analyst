# Community extension submission audit

## Source publication update — 2026-10-14

The owner authorized publication of the four preparation commits on `main`,
through `da0b34d98fdb290b27e512e122e3de88b6af687f`; the remote head was
verified. Earlier local/unpushed descriptions below are historical. This is
source publication only: no release tag, host installation, community submission
or workspace pin promotion was performed. Binary Ninja GUI registration,
minimum-host/platform compatibility and the provider/rendering acceptance gates
remain open; follow the existing release checklist before tagging a release.

Checked October 10, 2026 for release-readiness Phase 6. This is a source and
packaging review; it does not establish plugin-manager installation or approval.

## Submission route and sources

The requested [community-plugins repository](https://github.com/Vector35/community-plugins)
now marks its index deprecated for modern hosts and points to
[Binary Ninja Extensions](https://extensions.binary.ninja/). The current
[writing guide](https://docs.binary.ninja/dev/plugins.html) still describes a
GitHub release followed by an issue notifying Vector 35. Its linked submission
route is the community repository; prepare an issue, rather than a submodule PR,
and confirm the catalog destination with its maintainers. No issue was filed.

The audit checked the legacy
[INFO requirements](https://github.com/Vector35/community-plugins/blob/master/INFO),
the current guide, and the validator pinned to community-plugins commit
[`6e31fc84aaa7e62fe7ecbb7de5257c6235b9616b`](https://github.com/Vector35/community-plugins/blob/6e31fc84aaa7e62fe7ecbb7de5257c6235b9616b/generate_plugininfo.py).
The fetched validator's SHA-256 was
`66567ab31833fb3914e277d3cbf2ab437c820db08c353853fc66a984ca1392d5`.
Only its validation mode ran, from temporary scratch; no dependency was installed
and no generation/release workflow ran.

## Requirement-by-requirement result

| Requirement | Candidate evidence and result |
| --- | --- |
| Repository | Anonymous GitHub API confirmed `umbra-me/axio-analyst` is public, unarchived, with default branch `main`. Local preparation commits are not pushed. |
| Root metadata | `plugin.json` is at the repository root and parses. **Pass.** |
| Metadata format | `pluginmetadataversion` is integer `2`. **Pass.** |
| Name | `Axio Analyst`; no prohibited product/plugin suffix, within current 64-character limit. **Pass.** |
| Author | `Kian (Zenco)`; within current 128-character limit and aligned with README/license. **Pass.** |
| Short description | Shortened from 66 to 43 characters. Meets legacy INFO's under-50 guidance and current validator's 256-character ceiling. **Pass.** |
| Version | `0.9.1`; valid semantic version and within current 16-character limit. `core/version.py` reads it for all version surfaces. **Pass for source; no tagged release.** |
| API | `['python3']`; supported scripting API. **Pass.** |
| License | MIT name and full text; normalized text matches root LICENSE, excluding its title. **Pass.** |
| Minimum build | `minimumBinaryNinjaVersion: 4911` is a nonnegative integer build number and the current validator accepts this spelling. **Structural pass; compatibility at build 4911 is unverified.** |
| Platforms | Darwin/Linux/Windows are valid identifiers. **Structural pass; fresh platform acceptance remains open.** |
| Type | UI/helper categories match sidebar/assistance behavior. **Pass.** |
| Long description | Present, over 100 characters; modern manager will use it rather than README. **Pass.** Real media is still pending. |
| Installation instructions | Legacy INFO recommends a per-platform field; current validator says it is not displayed by modern hosts. Existing [setup instructions](setup.md) cover all three platforms. No ineffective metadata field was added. |
| Dependencies | Runtime uses standard library plus host-supplied Binary Ninja/PySide6. No pip requirements need installation; legacy `dependencies: {}` is not a CLI installer. Provider CLIs/authentication remain explicit external prerequisites. **Pass for source inventory.** |
| Install layout | Root `__init__.py`, metadata, and first-level runtime packages are present. A temporary `axio_analyst` copy reported current and all 36 manifest files matched source bytes. **Pass for isolated copier layout; actual manager loading is unverified.** |
| UI import order | Production entry reaches `ui/sidebar.py`, which imports `binaryninjaui` before PySide6 and before other Qt modules. **Pass by source inspection.** |
| Build artifacts | Pure Python plugin with painted artwork; no native plugin artifact is required. C++ demo builds are optional test material and ignored. **Pass for tracked layout.** |
| README and screenshots | Overview, quick start, security limits and maintainer are present. Screenshots/GIF are explicitly pending; future manager preview images need full GitHub URLs and its GIF preview is static. **Text prepared; captures pending.** |
| Official metadata validator | Pinned `generate_plugininfo.py -v plugin.json` printed `Successfully validated json file`. Its CLI does not signal validation failure through exit status, so the success output was checked too. **Pass.** |
| Tag and GitHub release | Required for ingestion; the manager reads metadata at the release tag's commit and uses its version. Local preparation is `0.9.1`; no tag/push/release performed. **Pending acceptance and approval.** |
| Submission | [Issue text](community-submission-draft.md) prepared with explicit missing release/compatibility evidence. No external issue/PR opened. **Draft only.** |

The legacy and current guidance differ on description length, optional metadata,
and installation instructions. The candidate satisfies both length rules; modern
validator behavior governs whether installation fields affect distribution.
Neither document converts a valid metadata file into a verified supported host.

## Remaining compatibility and publication gates

The October 10 post-change stock suite discovered 131 tests: 122 passed and
nine optional Qt tests were skipped. Compileall, metadata/runtime version,
142 relative documentation file links, whitespace and future-command syntax
passed. Runtime Python and tools are unchanged from the October 9 fixes; the
Phase 6 implementation changes are metadata and its regression contract. The
tracked credential/generated-file name check passed; it is not a full new
secret-content scan. No native Qt or live GUI run was added in this phase.

1. Verify the actual minimum supported Binary Ninja build. The existing floor
   was retained because this audit has no evidence for a replacement; do not
   describe `4911` as tested. In an isolated user profile on that build, follow
   G00/G01/G03/G04/G08/G18 in [the manual plan](manual-verification.md) and record
   host Python/Qt versions and registration failures. If unavailable or
   incompatible, choose a defensible tested floor and rerun its checks before
   submitting. Do not weaken compatibility rules to force installation.
2. Establish current-candidate platform support, including Windows Job Objects
   and a Linux host. Older Windows/macOS receipts do not accept the October
   patch. Record untested platforms honestly and decide the advertised support
   from evidence before publishing.
3. Complete the [release gates](release-preparation.md), then review the final
   diff/release notes and obtain explicit publication authorization. A metadata
   pass leaves the Codex, Markdown-resource and live-acceptance gates open.
4. After an approved release exists, test installation in a separate Binary
   Ninja user profile through the Extensions manager. Confirm the downloaded
   tag/commit and metadata, root package loading, version surfaces, manifest
   files, restart and the public-demo smoke case. Record that receipt separately
   from the temporary copier test; do not replace an existing workstation copy
   merely to make the test convenient. This is a distribution acceptance check
   after publication, not a requirement to claim before creating the first tag.
5. Fill the release URL, immutable commit and observed compatibility fields in
   the issue draft, resolve the catalog route with Vector 35 if needed, and
   obtain the user's explicit yes before sending it. This audit performs none
   of those outward actions.

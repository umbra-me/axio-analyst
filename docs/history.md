# Extraction history

Axio Analyst began as a custom plugin inside a personal Binary Ninja
configuration repository. That environment established two useful constraints:
the plugin had to coexist safely with unrelated user plugins, and installation
had to preserve licences, settings, symbols, and machine-local provider state.

The first configuration-repository commits that introduced the analysis
workflow were:

- `46710f2` - provider-neutral analysis sidebar;
- `f037f3c` - complete Ollama Cloud catalog discovery.

On 2026-08-08, the complete `0.7.0` working tree was extracted into this
standalone repository. The extraction included the Chat and Settings UI,
streaming and Markdown rendering, progress and cancellation, provider adapters,
tests, the bounded installer, architecture notes, and the C++ fixture. The
original configuration repository remained a workstation mirror rather than
the product source of truth.

On 2026-08-09, product-facing and internal identifiers were standardized:

- product and plugin metadata: **Axio Analyst**;
- Python package and installed plugin directory: `axio_analyst`;
- Binary Ninja settings group: `axioAnalyst`;
- test and sample names: `test_axio_analyst` and `axio_analyst_demo`;
- sidebar icon initials: `AX`.

Existing local settings were migrated to the new namespace and the live plugin
was installed under the new package directory. The standalone repository was
then documented for public initial publication at
`https://github.com/umbra-me/axio-analyst`.

Version `0.8.0` replaced the flat runtime module layout with first-level
packages for provider-neutral core and application logic, provider adapters,
Binary Ninja host integration, and Qt presentation. The test suite was split
to mirror those boundaries, and an explicit runtime manifest became the source
for development installation and drift checks. The same release made
`plugin.json` the validated semantic-version source and displayed it inside
Binary Ninja. The package-based runtime was installed and visually verified in
Binary Ninja Personal `5.4.10350-dev`; the obsolete flat modules were removed
through the installer's exact migration allowlist.

Version `0.9.0` added bounded opt-in context packs, evidence navigation,
off-by-default local transcripts, provider comparison, and usage accounting.
The unreleased September 5 change added explicit unverified findings and
schema-2 transcript/export provenance while retaining schema-1 read support;
its [dated change set](change-set-2026-09-05.md) preserves the live receipts.

The [October 9 change set](change-set-2026-10-09.md) records source fixes for
provider lifecycle, binary-bound callbacks, streaming, context extraction,
model discovery, and comparison cancellation. Version remained `0.9.0` at that
checkpoint.
Its regression evidence does not establish a new live installation, provider
inference result, tagged release, or publication.

On October 10, the maintainer selected `0.9.1` for the accumulated changes.
Metadata and current-version guidance were aligned, with a pending-release
changelog entry, [draft notes](release-notes-draft.md), and
[future tag/push commands](release-preparation.md). No tag or publication was
performed; historical live receipts still describe their earlier revisions.

No proprietary implementation, prompt, or data from Binary Ninja Sidekick was
used. Product direction is informed by the general category of integrated
reverse-engineering assistants, while Axio Analyst's code, prompts, process
contracts, and roadmap are independent.

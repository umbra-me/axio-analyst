# Axio Analyst

Axio Analyst brings provider-neutral AI assistance into Binary Ninja for reverse
engineers investigating functions and checking hypotheses. Inspect a bounded,
address-labelled context snapshot, then ask Claude Code, Codex, or Ollama Cloud
to explain it or compare their answers. The plugin stays read-only, keeps extra
context and local history opt-in, and leaves authentication with your installed
CLI.

## Quick start

You need Binary Ninja's Qt6 desktop UI and at least one supported, authenticated
provider CLI. The plugin uses Binary Ninja's bundled Python/PySide6 and adds no
third-party runtime dependencies.

1. Install this repository as `axio_analyst` in your Binary Ninja user plugin
   folder using the [platform-specific source-install commands](docs/setup.md#source-installation).
   For a separate checkout, use the [development installer](docs/setup.md#development-installation).
2. Authenticate Claude Code, Codex, or Ollama outside Binary Ninja. Choose a
   provider approved for the material you will send; read the
   [Codex confinement limitation](docs/providers.md#codex) before using that adapter.
3. Restart Binary Ninja, open an analyzed binary, and choose **Plugins > Axio
   Analyst > Open sidebar**. The harmless [demo fixture](samples/demo/README.md)
   is a useful first target.
4. Open **Settings**, select Provider, Model, and Reasoning, check the executable
   path, and choose **Apply**. Place the cursor in a function, open the composer's
   scope chip, and choose **Build preview** to inspect the context.
5. Choose a suggested question, type your own and press `Ctrl+Enter`, or use
   **More actions > Explain this function**. Check the answer against its cited
   IL addresses; provider output is unverified analysis.

The send control becomes **Stop** during a request. Every request rebuilds and
freezes its own context from the captured selection/options; a prior preview
does not lock later host analysis state.

## Features

- **Choose your provider.** Claude Code, Codex, and Ollama Cloud share one
  analysis interface, with editable models and provider-specific reasoning.
- **Inspect the context.** Address-labelled primary-function HLIL is included
  by default. Selection, up to three direct callers, five direct callees, twenty
  referenced strings/imports each, and relevant types are opt-in under one
  combined context-item character cap, with visible truncation.
- **Follow evidence.** Validated address citations navigate inside Binary Ninja;
  invalid addresses and ordinary provider links remain inert.
- **Keep claims reviewable.** Unverified findings retain bounded claims, supplied
  context excerpts, a context hash, and provider/version metadata.
- **Compare answers.** Run the active provider and one alternative sequentially
  over one frozen prompt, with separate results and usage summaries. This is
  qualitative comparison, rather than a benchmark.
- **Stay in the native workspace.** A compact sidebar provides context preview,
  progress, cancellation, a bounded literal-text streaming preview, and
  HTML-disabled terminal Markdown with wrapped code blocks.
- **Control local history.** Conversations stay in memory by default. Optional
  bounded restoration, explicit Clear deletion, and Markdown export are available.
- **See available accounting.** Measured duration and character counts are
  supplemented by token/cache/cost fields only when the provider reports them.

## Security model

The plugin does not rename symbols, change types, add comments, or write to the
BNDB. Its explicit prompt contains the binary's base filename, function metadata,
bounded selected context, and your question. Full source paths and whole binaries
are omitted; prompts go through stdin, and the plugin never reads provider
credential files. Local history is Off by default; saved/exported findings can
contain sensitive supplied context excerpts.

Provider output remains untrusted. HTML is disabled at Markdown import, and only
validated internal address links can navigate. CLI/provider retention is governed
by that provider. Codex's read-only sandbox and disabled shell/image/web tools
do **not** establish snapshot-only confidentiality; Markdown image/resource
loading and platform-specific cleanup also have remaining verification gates.
Use providers approved for your analysis material.

Read the [architecture and data boundaries](docs/architecture.md),
[security policy](SECURITY.md), and [exact provider contracts](docs/providers.md).

## Screenshots and walkthrough

Real captures are pending. These slots will show the public demo fixture after
the corresponding manual checks are recorded; no mock output is presented as a
completed run.

| Capture slot | Planned view | Target asset |
| --- | --- | --- |
| Screenshot pending | A completed function explanation beside the native HLIL, with valid evidence and an unverified finding footer. | `docs/media/sidebar-explanation.png` |
| Screenshot pending | The Request context workspace with a readable exact preview, enabled packs, counts, and truncation disclosure. | `docs/media/context-preview.png` |
| Screenshot pending | Two labelled provider results from a completed comparison over the public demo. | `docs/media/provider-comparison.png` |
| GIF pending | Inspect the preview, submit a question, then show the actual response and one validated address navigation. | `docs/media/inspect-explain.gif` |

The [capture plan](docs/capture-plan.md) specifies sizes, framing, steps, captions,
and the receipt required for each slot. Capture locally from the running plugin;
retain provider labels, unverified status, and relevant limitations.

## Project status

Source version is `0.9.1`, prepared as a release candidate with no tag or
published release. The [release preparation](docs/release-preparation.md)
records the pending gates and draft notes. The
[October 9 change set](docs/change-set-2026-10-09.md) records source fixes and
local regression evidence. Stock Python passed 121 tests with nine optional Qt
tests skipped; the bundled-Qt run passed all 130. Those source/widget checks do
not establish live Binary Ninja acceptance of the current changes.

The latest live receipt is still September 5. New observations are awaiting the
[manual verification plan](docs/manual-verification.md) and
[results template](docs/manual-verification-results-template.md); see the
[GUI verification index](docs/gui-verification.md) for completed and deferred
cases. Codex confinement, Windows cleanup, and Markdown resource behavior remain
open gates. No release-ready claim is made from the presentation changes.

Direct HTTP providers, credential/OAuth brokerage, indexing, agent tools, and
reviewable BNDB transformations remain [roadmap work](docs/roadmap.md).

## Documentation and development

- [Documentation index](docs/README.md)
- [Setup, upgrades, and removal](docs/setup.md)
- [Settings, context limits, and local storage](docs/configuration.md)
- [Provider commands and errors](docs/providers.md)
- [Development checks and release procedure](docs/development.md)
- [Release preparation and draft notes](docs/release-preparation.md)
- [Harmless demo build and function guide](samples/demo/README.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Current handoff](docs/handoff.md)
- [Changelog](CHANGELOG.md) and [contributing](CONTRIBUTING.md)

`plugin.json` is the single semantic-version source. Exact verification commands,
installer drift checks, and sample build instructions live in the linked guides.

## Maintainer and license

Maintained by **Kian (Zenco)** — [GitHub](https://github.com/notzenco) ·
[kian.pw](https://kian.pw).

Axio Analyst is independently implemented and is not affiliated with or based
on proprietary Binary Ninja Sidekick code, prompts, or data. It is available
under the [MIT License](LICENSE).

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

No proprietary implementation, prompt, or data from Binary Ninja Sidekick was
used. Product direction is informed by the general category of integrated
reverse-engineering assistants, while Axio Analyst's code, prompts, process
contracts, and roadmap are independent.

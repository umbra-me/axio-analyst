# September 5 change set

## Structured findings — 2026-09-05

Responses now carry up to 64 structured findings extracted from paragraphs with
addresses. Each records a bounded claim, up to 256 addresses, an exact supplied
context excerpt, a SHA-256 of the frozen context bundle, analysis version,
provider/model, and an explicit `unverified` status. Extraction does not establish
that a claim is true. `Finding.stale` can compare a later context digest; automatic
stale-state UI and structured claim adjudication remain future work.

Conversation schema 2 stores findings and reads schema 1 records. Finding metadata
is validated on reads and writes; imported records cannot claim verified status.
Persistence remains opt-in, Clear deletes the fingerprint record, and Markdown
export includes claims, provenance and excerpts. Unlike schema 1, stored/exported
records can now contain bounded supplied context excerpts; credentials, complete
binary bytes and BNDB mutation remain outside the feature.

Transcript load/complete/save paths preserve findings, and the footer reports
the unverified finding count and context hash prefix. Runtime installation includes
`core/findings.py`. Deterministic fixtures cover context changes, schema migration,
storage/export/deletion, and streaming/cancellation without provider calls.

Verification: 59 stock-Python 3.13 tests passed. Python 3.9 cannot load existing
union annotations and is not a valid test environment. The installed development
plugin matched the source. Binary Ninja Personal 6.1.10608-dev on macOS opened
the bundled Mach-O demo and registered the sidebar. A 7,418-character current
function context preview was inspected with optional packs disabled. One benign
request through the existing Ollama Cloud provider rendered three explicitly
unverified findings, the context hash prefix `bdc85f92de66`, and provider usage.
Activating a transcript citation moved the native selection from
`0x100000d30–0x100000d34` to `0x100000d44–0x100000d48`.

Binary Ninja was quit and reopened; reopening the demo restored the sidebar,
current function and existing provider/model configuration. With persistence Off,
the prior conversation was absent as expected. Settings were inspected but not
applied; no credentials, binary bytes or BNDB edits were exported. Provider
switching, persistent-conversation restart and cancellation during an active
request remain distinct unverified UI cases. Version remains 0.9.0 with no release
tag or BNDB mutation.

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
union annotations and is not a valid test environment. Real Binary Ninja sidebar
acceptance of these changes, citation navigation, restart and provider UI flows
remain unverified. The previous implementation copied the runtime into the local
development plugin directory; that does not establish GUI acceptance. Version
remains 0.9.0, with no release tag or BNDB mutation.

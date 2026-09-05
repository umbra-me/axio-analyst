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
request were still unverified at that checkpoint; the follow-up below updates two. Version remains 0.9.0 with no release
tag or BNDB mutation.

## Native cancellation and persistence follow-up

On September 5, the real Binary Ninja Personal 6.1.10608-dev GUI reopened only
`samples/demo/build/axio_analyst_demo`. Local history was enabled through the
Analyst settings checkbox and Apply. The current-function-only public demo prompt
contained the unique marker `AXIO-PERSIST-20260905` and requested a one-sentence
explanation; no unrelated binary or optional context pack was used.

The native accessibility state showed request progress 35, the Stop request
control and “starting ollama cloud”. Clicking Stop returned progress to zero and
replaced Stop with the idle Send control. Binary Ninja was then quit using its
normal keyboard command, relaunched and the exact demo reopened through its
file dialog. The native screenshot visibly restored the marker and the response
“Request cancelled before a response was received”, attributed to Ollama Cloud /
`glm-5.3-flash:cloud`. This proves cancellation before a response and persistence
of that cancelled conversation across a real application restart. It does not
claim mid-stream partial-output cancellation or successful-response persistence
was independently exercised in this follow-up.

The Local history checkbox was then unchecked and Apply saved the original Off
setting; the final native accessibility state confirmed Off and checkbox value 0.
Provider/model remained Ollama Cloud / `glm-5.3-flash:cloud`, reasoning Default,
limits 300 seconds / 60,000 characters. The bounded demo transcript may remain in
local storage while persistence is Off; no saved transcript was published or
cleared through a destructive action.

Provider switching remains unverified. The provider dropdown did not change
through native accessibility clicks, keyboard selection or screenshot-coordinate
fallbacks, while the history/Apply/Send/Stop controls did work. Initial screenshots
lagged accessibility changes; only the post-restart screenshot is relied on for
visible transcript evidence. No alternative OS automation or settings-file edits
were used to bypass the UI. This is an acceptance-tooling limitation, not evidence
that switching works or that the application necessarily has a provider bug.

Only this receipt changed; no implementation tests were rerun for documentation.

# README capture plan

Prepared: 2026-10-09. All assets below are **pending real capture**. This plan
creates no screenshot, provider response, or verification receipt.

Use the harmless [demo fixture](../samples/demo/README.md) and the
[manual verification plan](manual-verification.md). Capture the actual installed
candidate after the relevant checks pass; record its source revision, installed
status, Binary Ninja build, platform, CLI/model/effort, fixture SHA-256, function,
context options, and date/time. The current runtime fixes still lack a new live
GUI receipt. Do not treat the September observations as proof of a later build.

## Common framing

- Export each still as a **1600 × 1000 px PNG**, with no scaling of the completed
  image. On a Retina display a capture may have twice the logical screen pixels;
  verify the exported file's pixel size and crop/recapture deliberately.
- Allocate about **1040 px** to native HLIL and **520 px** to the sidebar, with
  remaining space for native chrome/dividers. For the context and comparison
  shots a **640 px** sidebar may be clearer; keep the total image size the same.
- Use one readable host theme consistently, a readable font, and the public
  function's name/address. Hide unrelated tabs, account names, private paths,
  desktop notifications, and other applications before recording.
- Leave the provider/model label, evidence links, usage, and **unverified** status
  visible wherever they are relevant. Do not retouch an answer, invent a footer,
  remove a failure to make a run appear successful, or describe a crop as the
  full transcript.
- Preserve an unedited original locally. Crop only for framing, and record any
  resizing, redaction, trimming, or frame-rate conversion in the capture receipt.
  Redaction must not hide a behavior relevant to the claim in the caption.
- No credential screens, proprietary binaries, real malware, synthetic model
  answers, or fabricated benchmark/usage figures belong in these assets.

## Still shot list

| Asset | Exact state and action | Evidence prerequisite | Size |
| --- | --- | --- | --- |
| `docs/media/sidebar-explanation.png` | Select `validate_access_code` or another named public demo function with readable HLIL. Use primary-only context and one permitted provider. Complete a cited explanation. Position the answer so its claim, valid evidence link, actual provider/model, and unverified finding footer are visible beside the native function. | G04 response and G08 valid evidence navigation observed for this candidate; record the exact function and actual answer. If there is no finding, do not claim one in the caption. | 1600 × 1000 PNG; sidebar about 520 px. |
| `docs/media/context-preview.png` | Open the scope chip. Enable only the packs the screenshot will disclose, then Build preview. Show the checked options, item/character summary, and readable exact address-labelled text. For visible truncation use the 1,000-character test cap on a sufficiently large demo function; restore the original cap afterward. | G03 preview/budget observations, including the actual truncation marker if the caption mentions truncation. Do not claim an all-pack complete view when only a scrolled subset is shown. | 1600 × 1000 PNG; sidebar about 640 px. |
| `docs/media/provider-comparison.png` | Choose a permitted primary and alternative under More actions > Compare with. Complete the run on one unchanged demo context. Position the transcript so both provider headings and actual accounting are readable; retain the actual unverified/context footer. If both sections cannot fit, crop a labelled excerpt or make two supplemental stills. | G07 success for the exact pair, plus the recorded context/hash. One preview/hash is not independent proof of the stdin bytes sent to both processes. | 1600 × 1000 PNG; sidebar about 640 px. |

The default captions are templates, not observations:

```text
Explanation: <provider/model> explains <demo function> from <N> context items
and <M> item-text characters. Findings are unverified; <address> was checked
against the native view. Captured <date> on <revision>/<Binary Ninja build>.

Context: The request workspace exposes <enabled packs>, <N> items, <M>
characters, and <actual truncation state>. The excerpt shown is <full/cropped>.
Each request rebuilds its snapshot before dispatch.

Comparison: <primary> and <alternative> return separate answers and actual
usage over one frozen request context. This is qualitative inspection;
provider claims require manual validation. Captured <date>/<revision>.
```

Replace placeholders only with recorded facts. A model's answer is not an
independently verified conclusion merely because the screenshot includes it.

## Short GIF — inspect, explain, navigate

Target: `docs/media/inspect-explain.gif`, **1280 × 800 px**, about **10 fps**,
**15–20 seconds** final duration, with one consistent crop. Record the real
desktop at that pixel size if possible; if a larger source is downscaled, record
the source size and check that HLIL, labels, and the footer remain readable.
An existing screen recorder is sufficient; this plan adds no capture dependency.

1. **0–3 s:** show the public function and idle Axio Analyst sidebar. Open the
   composer's scope chip. Do not start with an already-running unexplained job.
2. **3–6 s:** Build preview and pause on its actual options, item/character
   totals, and readable text. Return to the conversation.
3. **6–9 s:** submit a short cited explanation question. Show the real transition
   from Send to Stop and the actual phase/progress indicator.
4. **9–15 s:** show actual output arriving or the completed response. Codex's
   adapter may expose a final message rather than text deltas; retain what the
   chosen provider actually does. Do not fabricate streaming.
5. **15–20 s:** activate one validated evidence link and show the native view
   move to that address, leaving provider/unverified metadata visible.

The timeline is an editorial target, not a latency claim. If inference takes
longer, record the whole run and trim only idle waiting. Mark the visible edit
and caption it **“Idle wait shortened; not a latency benchmark.”** Keep the
actual inference duration in the receipt. Never speed up or splice separate
requests to imply one continuous faster response. If the interactions cannot
fit legibly into 20 seconds, retain a longer original and use a labelled shorter
excerpt rather than claiming the whole flow was shown.

The GIF uses one provider; the comparison still covers the separate comparison
feature. A successful GIF does not establish every provider's behavior or close
the Codex confidentiality, Windows cleanup, or Markdown resource-loading gates.

## Capture receipt

Keep one receipt per asset in local notes until reviewed:

```text
Asset filename:
Observed date/time/timezone:
Source revision and any dirty runtime/metadata changes:
Installed runtime status and Binary Ninja build:
OS/architecture/theme:
Fixture SHA-256 / function / start address:
Provider(s) / CLI version(s) / model(s) / effort(s):
Context options / item count / total characters / truncation:
Actual question and response (public demo only):
Validated citation and native before/after addresses:
Unverified finding count/context hash, if present:
Manual test case and evidence reference:
Original / exported pixel sizes, format, duration and fps:
Crop/redaction/resizing/idle-wait edits:
Actual inference duration, if video waiting was shortened:
Caption filled with observed facts:
Remaining untested behavior:
```

## Replacing README placeholders

Add only reviewed real assets under `docs/media/`. Replace each pending table
row with its actual image/GIF embed and observed caption. Update the GUI receipt
only for the checks actually observed; do not infer unrelated passes from a
presentation asset. If a capture reveals a failure, keep the slot pending and
report the failure for a source fix and fresh verification.

The README author links and copyright identify **Kian (Zenco)**. Asset captions
must not add model or assistant authorship claims.

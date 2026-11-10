# Public walkthrough candidates

Prepared October 10, 2026 for release-readiness Phase 7. **Target choice is
pending.** Only public documentation and sample-list metadata were read. No
target was downloaded, built, executed or analyzed; no findings are claimed.

## Three options

| Target | What the planned walkthrough could demonstrate | Tradeoff and evidence source |
| --- | --- | --- |
| **cJSON parser — recommended** | Build the upstream `parse_examples` test executable with the C library linked statically. Investigate one parsing function, compare primary-only and optional caller/type context, then check each AI claim against IL and the exact matching source. | Small enough for a focused post with inspectable source and reproducible build identity. It demonstrates input-boundary reasoning without asserting a vulnerability. cJSON documents explicit-length parsing; its [test CMake file](https://github.com/DaveGamble/cJSON/blob/master/tests/CMakeLists.txt) defines `parse_examples`. See [upstream project](https://github.com/DaveGamble/cJSON). |
| **SQLite command-line binary** | Pick a narrow tokenization or query-preparation path in a locally built, version-pinned CLI. Demonstrate truncation, selecting relevant neighbours, and revising an AI hypothesis after manual source/IL checking. | A larger real application makes scope control visible, but one snapshot cannot explain the whole database engine. Source amalgamation and shell construction are documented by SQLite; see [architecture](https://sqlite.org/arch.html) and [amalgamation](https://sqlite.org/amalgamation.html). |
| **Mirai-labelled sample from MalwareBazaar** | Plan a static-only investigation of one user-selected sample's configuration or networking-related routine, with address-by-address manual validation and explicit uncertainty. | Adds malware-analysis relevance but requires the user's isolated VM, matching architecture support and careful network separation. The [family listing](https://bazaar.abuse.ch/browse/signature/Mirai/) provides candidates; its label is not proof of behavior in a selected binary. Mirai has public defensive context in [CISA's IoT resilience report](https://www.cisa.gov/sites/default/files/publications/NSTAC%20Report%20to%20the%20President%20on%20ICR%20FINAL%20%2810-12-17%29%20%281%29-%20508%20compliant_0.pdf). No sample hash is selected and no sample bytes were handled. |

These are proposed demonstrations, inferred from the source/documentation and
the plugin's current workflow. They are not findings, completed analyses, or
evidence of eligibility for any verification program. For either open-source
target, select an immutable upstream revision and record build flags/toolchain
and binary SHA-256 before making address-level claims.

## Work after the user chooses

Prepare a target-specific outline and safe-handling procedure, preserving this
post structure:

1. **Setup:** [chosen revision/sample page, verified SHA-256, architecture,
   Binary Ninja/plugin commit and versions, isolation and provider configuration].
2. **Axio context snapshot:** [function/address, exact enabled packs, item and
   character counts, truncation notices, question and frozen-context hash].
3. **AI findings:** [actual labelled response and unverified findings; no
   prewritten conclusions, fabricated tokens or duration].
4. **Manual validation:** [each claim, cited IL address, observed instructions,
   source or other independent evidence, supported/refuted/inconclusive result].
5. **Conclusions and limitations:** [what was actually learned, missed context,
   failed hypotheses, provider limitations and unanswered questions].

For a malware choice, only the user handles the sample in a disposable isolated
VM: snapshot before introduction, disable network and shared folders/clipboard,
verify hashes inside the guest, prefer static analysis, and revert after saving
only reviewed text/captures outside it. Dynamic behavior or a controlled sinkhole
would require a separate explicit plan; no public-internet execution is proposed.
Cloud CLIs cannot be invoked from a network-disabled guest. Keep that boundary
intact and design any provider step separately; do not enable general egress to
make the walkthrough work. The Codex confidentiality gate remains relevant even
for public targets.

The target-specific procedure and real-results ledger will follow the choice.
Keep every observation slot unfilled until the user supplies dated results.

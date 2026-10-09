# Documentation

This directory contains the maintained technical and operational documentation
for Axio Analyst. The root [README](../README.md) is the product overview and
quick start; these documents are the source of truth for detailed behavior.

## Document map

| Document | Owns |
| --- | --- |
| [Setup and installation](setup.md) | Prerequisites, source and development installs, upgrades, removal, and first-run validation. |
| [Configuration reference](configuration.md) | Every `axioAnalyst.*` setting, defaults, ranges, persistence, and UI behavior. |
| [Provider contracts](providers.md) | Child-process commands, authentication boundary, input/output parsing, discovery, limits, and errors. |
| [Architecture](architecture.md) | Current dependency boundaries, module responsibilities, threading, data flow, and security model. |
| [Roadmap](roadmap.md) | Product end state, current limitations, and future delivery phases. |
| [Sidekick capability inventory](sidekick-capability-inventory.md) | Dated, source-backed inventory of the Sidekick reference product, including analysis, UI, storage, permissions, automation, privacy, and implications for Axio. |
| [Development and release guide](development.md) | Repository workflow, tests, extension points, manual GUI checks, and release procedure. |
| [GUI verification](gui-verification.md) | Dated real-host evidence, deferred interaction checks, fixture launch safety, and the current application-updater observation. |
| [Manual verification plan](manual-verification.md) | Candidate installation, precise deferred-case steps, expected results, and evidence to record in Binary Ninja Personal. |
| [Verification results template](manual-verification-results-template.md) | Unfilled run identity, per-provider case ledger, observed receipts, and untested gates. |
| [Troubleshooting](troubleshooting.md) | Startup, sidebar, Binary Ninja updater, provider, model discovery, timeout, rendering, and recovery diagnostics. |
| [Current handoff](handoff.md) | Dated implementation, live-install state, verification evidence, protected boundaries, and next work. |
| [October 9 change set](change-set-2026-10-09.md) | Release-readiness source fixes, regression evidence, unchanged version, and open acceptance/security gates. |
| [September 5 change set](change-set-2026-09-05.md) | Historical structured-findings/schema-2 implementation and dated native cancellation/persistence receipts. |
| [Extraction history](history.md) | Provenance of the standalone repository, naming transition, and package migration. |

Repository-level policy documents remain at the root:

- [Security policy](../SECURITY.md)
- [Contributing guide](../CONTRIBUTING.md)
- [Changelog](../CHANGELOG.md)
- [Repository instructions](../AGENTS.md)

## Maintenance rules

- Update the document that owns a behavior in the same change as the code.
- Keep exact commands executable from the repository root unless the document
  explicitly changes directories.
- Record current behavior in the present tense. Put past release behavior in
  `CHANGELOG.md` or `history.md` instead of leaving stale notes in setup docs.
- Keep the current implementation and future roadmap clearly separated.
- Keep the current semantic version consistent with `plugin.json`; other docs
  describe or link that source rather than defining an independent value.
- Do not place credentials, proprietary binary material, machine-local settings
  values, or provider transcripts in documentation.
- A handoff is a dated operational snapshot. Refresh it when repository,
  installation, verification, or blocker state changes materially.
- Keep dated verification receipts attached to the source and environment they
  exercised. New source tests do not establish a live installation or release.

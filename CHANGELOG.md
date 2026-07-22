# Changelog

All notable changes to this project will be documented here.

## [0.2.0] - 2026-07-22

### Added

- Agent-driven bootstrap installation in an isolated virtual environment.
- `rrc setup` for Codex, Claude Code, or both at user or project scope.
- `rrc doctor` for runtime, PDF backend, and skill installation checks.
- Self-contained skill bundles with the report schema and generated runtime path.
- A copy-paste installation prompt for researchers already using an agent.
- Package-resource and installation regression tests.

### Changed

- The primary user experience now stays inside the researcher's existing agent instead of requiring a separate application.

## [0.1.0] - 2026-07-22

### Added

- R0-R3 verified reading-level specification.
- PDF manifest and controlled page-reading commands.
- Hash-chained page-access receipt ledger.
- Independent report verifier with automatic level downgrade.
- Claim-to-page receipt checks and optional exact quote verification against the PDF.
- JSON report schema, installable agent skill, examples, and regression tests.

### Boundaries

- Receipt validity establishes recorded source exposure within a trusted harness, not comprehension.
- Claim grounding establishes traceability to quoted spans, not scientific truth or literature consensus.

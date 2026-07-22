# Research Reading Contract

Research Reading Contract (RRC) is a small, model-agnostic protocol for making scientific PDF reading claims auditable.

It addresses a common failure mode in research agents: an answer says it read the full paper when the model saw only an abstract, a few retrieved chunks, or an unverified summary. RRC separates three questions that are often blurred together:

1. **Coverage:** which pages were actually exposed to the agent?
2. **Grounding:** which source spans support each substantive claim?
3. **Truth:** is the claim scientifically correct?

RRC verifies the first two. It does **not** prove comprehension, scientific truth, or methodological quality.

## What it does

- fingerprints a PDF and records its page count;
- extracts requested pages through a controlled reader;
- appends hash-chained page-access receipts to a local JSONL ledger;
- verifies claimed reading levels against those receipts;
- checks claim-to-page anchors and, when the PDF is supplied, exact quoted spans;
- downgrades unsupported `FULL_TEXT_VERIFIED` claims instead of trusting model self-report.

## Reading levels

| Level | Meaning | Minimum verification |
|---|---|---|
| `R0_DISCOVERED` | The source is known, but content access is unverified. | Source identity only. |
| `R1_ABSTRACT_VERIFIED` | Declared abstract pages were accessed. | Valid receipts for all `abstract_pages`. |
| `R2_TARGETED_VERIFIED` | A bounded question was investigated in declared pages/sections. | Target question plus valid receipts for all `required_pages`. |
| `R3_FULL_TEXT_VERIFIED` | Every page in the PDF was accessed. | Valid receipts for all pages in the source PDF. |

`R3` is intentionally strict. A model cannot grant it to itself by writing `full_text` in JSON.

## Quick start

```bash
python -m pip install -e .

# Fingerprint the source.
rrc manifest paper.pdf

# Read pages through the controlled reader and record receipts.
rrc read paper.pdf --pages 1-3 --ledger .rrc/access.jsonl

# Verify an agent-produced report.
rrc verify report.json --ledger .rrc/access.jsonl --pdf paper.pdf
```

The verifier exits non-zero when the report is not publishable at its claimed level. Its JSON output still explains the granted level, missing coverage, grounding failures, and warnings.

## Report contract

An agent writes a report conforming to [`schemas/reading-report.schema.json`](schemas/reading-report.schema.json). The minimal structure is:

```json
{
  "protocol_version": "0.1",
  "report_id": "review-001",
  "source": {
    "sha256": "<pdf sha256>",
    "page_count": 12,
    "title": "Example paper"
  },
  "reading": {
    "claimed_level": "R2_TARGETED_VERIFIED",
    "target_question": "What evidence supports the primary endpoint?"
  },
  "coverage": {
    "abstract_pages": [1],
    "required_pages": [1, 4, 5, 9],
    "required_sections": ["Methods", "Results"],
    "sections_read": ["Abstract", "Methods", "Results"]
  },
  "claims": [
    {
      "claim_id": "C1",
      "claim_text": "The intervention improved the primary endpoint.",
      "epistemic_status": "direct",
      "evidence_refs": [
        {
          "page": 5,
          "section": "Results",
          "quote": "The primary endpoint improved ...",
          "support_type": "supports"
        }
      ]
    }
  ],
  "answer_status": "provisional",
  "limitations": ["No supplementary file was available."]
}
```

See [`SPEC.md`](SPEC.md) for normative rules and [`skills/research-reading-contract`](skills/research-reading-contract) for an installable agent skill.

Release history is recorded in [`CHANGELOG.md`](CHANGELOG.md).

## Trust boundary

The receipt ledger is hash-chained to reveal accidental edits and partial corruption. It is not a cryptographic proof that a hostile process read a page. Strong enforcement requires the agent harness to expose `rrc read` as the only PDF-content channel and keep the ledger outside the model's write permissions.

## Why this is a separate project

RRC is deliberately narrower than a literature-review agent, memory system, or scientific consensus engine. Any agent can use it: Codex, Claude, Hermes, local models, multi-agent workflows, or a custom MCP server. The protocol constrains the evidence boundary without prescribing the reasoning model.

## Status

Version `0.1.0` is a working reference implementation and a proposal for community discussion. The schema may evolve before `1.0`.

## License

MIT. See [`LICENSE`](LICENSE).

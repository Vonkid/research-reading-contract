---
name: research-reading-contract
description: Use when reading, summarizing, comparing, reviewing, or citing scientific PDFs where page coverage and claim-to-source traceability matter. Enforces verified R0-R3 reading levels, page-access receipts, evidence quotes, and explicit downgrade rules before an agent claims abstract, targeted, or full-text review.
---

# Research Reading Contract

Use the RRC command-line verifier as an external evidence boundary. Never infer a reading level from confidence, document length, retrieved snippets, or a prior model's statement.

## Workflow

1. Fingerprint the exact PDF:

   ```bash
   rrc manifest PAPER.pdf
   ```

2. Choose the smallest level that can answer the task:

   - `R0_DISCOVERED`: identify or triage the source without content claims.
   - `R1_ABSTRACT_VERIFIED`: summarize only the abstract.
   - `R2_TARGETED_VERIFIED`: answer one declared question from selected pages and sections.
   - `R3_FULL_TEXT_VERIFIED`: review the complete PDF page by page.

3. Read content only through the receipt-producing reader:

   ```bash
   rrc read PAPER.pdf --pages 1-3,7 --ledger .rrc/access.jsonl
   ```

4. Build a report matching `schemas/reading-report.schema.json`. For each substantive claim:

   - distinguish `direct`, `author_interpretation`, and `inference`;
   - include the source page and a verbatim evidence quote;
   - label the quote as `supports`, `contradicts`, `qualifies`, or `context`;
   - state limitations and use `insufficient_evidence` when coverage cannot support the answer.

5. Verify outside the reasoning step:

   ```bash
   rrc verify report.json --ledger .rrc/access.jsonl --pdf PAPER.pdf
   ```

6. Report the verifier's `granted_level`, never the model's unverified `claimed_level`. If verification fails, fix the report or downgrade the answer.

## Non-Negotiable Rules

- Do not claim `R3_FULL_TEXT_VERIFIED` unless every PDF page has a valid receipt.
- Do not treat search results, abstracts, summaries, or retrieval chunks as full text.
- Do not cite a page that lacks a valid receipt.
- Do not turn paraphrased memory into an evidence quote.
- Do not describe receipt validity as comprehension or scientific correctness.
- Keep paper quality, cross-paper consensus, and methodological critique as separate analyses.

## User-Facing Output

Include a compact reading declaration with:

- granted level;
- pages accessed and pages missing for the requested level;
- answer status;
- material limitations.

Do not narrate internal receipt mechanics unless the user asks. The scientific answer remains primary.

## Reference

Read [references/protocol.md](references/protocol.md) when implementing this skill in a new harness or deciding how to map a task to R0-R3.

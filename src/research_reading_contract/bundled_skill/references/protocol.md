# Protocol Reference

## Task-to-level mapping

| Task | Default level | Notes |
|---|---|---|
| Find or deduplicate a citation | R0 | Do not make content claims. |
| Abstract screening | R1 | Limit conclusions to abstract content. |
| Check one method, result, or citation | R2 | Declare the target question and required pages. |
| Review, reproduce, or comprehensively summarize one paper | R3 | Access every page and ground substantive claims. |
| Synthesize multiple papers | Per-source R1-R3 | Record a level independently for every source. |

## Evidence semantics

- `direct`: the paper reports the statement, result, or method.
- `author_interpretation`: the paper's authors make the interpretation.
- `inference`: the agent derives a synthesis not directly stated by the source.

The label describes who owns the inference. It does not assign truth.

## Downgrade policy

- Missing abstract receipts: R0.
- A targeted question without complete required-page receipts: at most R1.
- Any unread PDF page: at most R2.
- A claim without a page receipt and source quote: claim grounding fails even if coverage passes.
- A quote absent from the supplied PDF page: claim grounding fails.

## Harness integration

For enforcement, expose `rrc read` as the agent's PDF reader, protect the JSONL ledger from model writes, and run `rrc verify` in a separate process. A prompt-only installation improves behavior but cannot establish trusted receipts.

# Research Reading Contract Specification 0.1

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as normative requirements.

## 1. Scope

This specification defines:

- source identity and page-access receipts;
- verified reading levels;
- claim-to-evidence anchors;
- downgrade and publication rules.

It does not define whether a scientific claim is true, whether a paper is high quality, or whether an agent understood the content.

## 2. Source identity

A source MUST be identified by the SHA-256 digest of the exact PDF bytes and its page count. A report verified against a different digest MUST fail source validation.

## 3. Access receipts

An access receipt MUST contain:

- protocol version;
- unique event ID;
- UTC timestamp;
- source SHA-256;
- one-based page number;
- SHA-256 of extracted page text;
- extracted character count;
- previous event digest;
- current event digest.

The current event digest MUST be computed over the canonical JSON representation of all event fields except the digest itself. A verifier MUST reject an invalid chain from the first broken event onward.

Receipts establish recorded exposure inside the harness trust boundary. They do not establish attention or comprehension.

## 4. Reading levels

### R0_DISCOVERED

The source is identified, but no content coverage is asserted.

### R1_ABSTRACT_VERIFIED

The report MUST declare one or more `abstract_pages`. Every declared abstract page MUST have a valid receipt for the source.

### R2_TARGETED_VERIFIED

The report MUST declare:

- a non-empty `target_question`;
- one or more `required_pages` selected for that question;
- valid receipts covering every required page.

If `required_sections` are declared, each MUST appear in `sections_read`.

R2 means the question received bounded, traceable investigation. It MUST NOT be described as a full-paper review.

### R3_FULL_TEXT_VERIFIED

Every page from `1` through the source `page_count` MUST have a valid access receipt. When the source PDF is supplied to the verifier, its digest and page count MUST match the report.

R3 means full PDF page exposure. It MUST NOT be represented as proof of comprehension, truth, reproducibility, or review quality.

## 5. Claims and evidence

Every substantive claim in a `complete` or `provisional` answer MUST contain at least one evidence reference. Each reference MUST include:

- one-based page number;
- a non-empty quote;
- support type: `supports`, `contradicts`, `qualifies`, or `context`.

The referenced page MUST have a valid access receipt. When the PDF is supplied, the normalized quote MUST occur on the referenced page. Paraphrases MAY appear in `claim_text`, but the evidence `quote` MUST be source text.

The report MUST label each claim as:

- `direct`: stated or measured in the source;
- `author_interpretation`: interpretation explicitly made by the paper's authors;
- `inference`: synthesis made by the reporting agent.

## 6. Verification output

A verifier MUST report separately:

- claimed reading level;
- granted reading level;
- coverage failures;
- claim-grounding status;
- source-validation status;
- publishability at the claimed level.

A lower granted level is not itself an error. Presenting the higher claimed level after downgrade is an error.

## 7. Answer states

- `complete`: the answer claims sufficient evidence for the requested scope.
- `provisional`: the answer is usable with explicit limitations.
- `insufficient_evidence`: the available source coverage cannot support an answer.

An `insufficient_evidence` report MAY contain no substantive claims. Other answer states MUST contain grounded claims.

## 8. Harness guidance

For meaningful enforcement, a harness SHOULD:

- provide PDF text only through a receipt-producing reader;
- prevent the model from editing the receipt ledger;
- run verification outside the model process;
- display the granted level, not the self-reported level;
- retain the report and ledger with the research artifact.

## 9. Non-goals

RRC MUST NOT be used as evidence that:

- the model understood all exposed text;
- a claim is scientifically true;
- a citation is relevant beyond the quoted span;
- a review is unbiased or complete across the literature;
- consensus exists.

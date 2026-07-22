# Contributing

Contributions are welcome, especially adversarial examples that reveal false grants or unjustified downgrades.

## Principles

- Keep coverage, grounding, and truth as separate outputs.
- Do not add model-specific assumptions to the core protocol.
- Prefer machine-checkable rules over prompt-only instructions.
- Add a regression test for every verifier behavior change.
- Do not commit copyrighted papers, private paths, credentials, or unpublished research data.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

Changes to `schemas/reading-report.schema.json` or `SPEC.md` should explain compatibility impact.

# Security

Please report security issues privately through GitHub's security advisory feature.

## Trust model

The JSONL receipt chain detects broken or edited chains but is not a signature. A process with permission to rewrite the entire ledger can forge a new valid chain. Production harnesses should keep ledgers outside model write access and execute verification in a separate trusted process.

Do not place API keys, unpublished PDFs, sensitive excerpts, or private filesystem paths in public reports or issues.

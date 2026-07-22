# Small-Group Pilot Guide

RRC is designed to be tested inside a researcher's existing Codex or Claude Code workflow. Do not ask participants to adopt another chat application.

## What to send

Send the repository link and this prompt:

```text
Install Research Reading Contract for the agent you are currently running.
Repository: https://github.com/Vonkid/research-reading-contract
Read AGENT_INSTALL.md and follow the user-scope procedure. Use an isolated
environment, run the final doctor check, and report the installed path. Do not
request API keys, upload papers, or modify unrelated agent settings.
```

## First task

After installation, ask the participant to attach a paper they already know and run:

Codex:

```text
$research-reading-contract Check one central claim in this PDF. Use the smallest
adequate verified reading level, show the source quote and page, and state what
the current coverage cannot support.
```

Claude Code:

```text
/research-reading-contract Check one central claim in this PDF. Use the smallest
adequate verified reading level, show the source quote and page, and state what
the current coverage cannot support.
```

## What to evaluate

Ask four questions after one real task:

1. Did installation complete without manual troubleshooting?
2. Did the agent discover and use RRC without explaining internal machinery?
3. Did the page quote and limitation make the answer more trustworthy or merely longer?
4. Did an automatic downgrade prevent a claim the participant would otherwise have accepted?

The pilot succeeds only if the workflow is easier than manually checking the agent's reading behavior.

## Privacy

Installation does not require an API key and does not inspect a paper. During use, RRC stores its receipt ledger under the working project's `.rrc/` directory. The model provider still receives whatever PDF content the researcher's existing agent normally sends; RRC does not change that provider's data policy.

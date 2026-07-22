# Install RRC From an Agent

This guide is written for Codex or Claude Code to execute on behalf of its user.

## Safety boundary

- Install into an isolated virtual environment.
- Do not request or modify API keys.
- Do not upload or inspect the user's papers during installation.
- Do not alter unrelated agent settings, shell profiles, or Python environments.
- Only write the RRC environment and the selected agent's RRC skill directory.

## Procedure

1. Clone this repository into a temporary working directory.
2. Identify the current agent:
   - Codex: use `--agent codex`.
   - Claude Code: use `--agent claude`.
   - Configure both only when the user explicitly asks: use `--agent both`.
3. Run the bootstrap script.

macOS or Linux:

```bash
python3 scripts/bootstrap.py --agent codex
```

Windows PowerShell:

```powershell
py -3 scripts\bootstrap.py --agent codex
```

Replace `codex` with `claude` when appropriate. User scope is the default. Do not use `--force` unless an existing unrecognized destination has been inspected and the user approves replacement.

4. Require the final `doctor` result to report `"ready": true`.
5. Tell the user where the skill was installed and whether an agent restart is needed.

## Invocation

- Codex: mention `$research-reading-contract` in the task.
- Claude Code: invoke `/research-reading-contract` or ask Claude to use it.

Do not explain the internal ledger unless asked. Start with the user's scientific reading task.

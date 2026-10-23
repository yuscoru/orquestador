---
name: ado-work-items
description: Create and read back Azure DevOps Tasks under approved Change Requests, query children, and add sanitized completion comments using az boards.
disable-model-invocation: true
---

# Azure DevOps Work Items skill (`ado-work-items`)

Audited project skill providing deterministic, idempotent Task creation and read-back for change delivery.

## Authority & constraints

- Must be invoked explicitly (`disable-model-invocation: true`).
- Uses local script `scripts/ado_cli.py`.
- Reads PAT exclusively from `AZURE_DEVOPS_PAT` in environment (sourced from root-only mode 0600 `/root/.pi-team/env.sh`).
- Never logs, prints, echoes or passes PAT in command line arguments (`az` CLI uses `AZURE_DEVOPS_EXT_PAT` in memory).
- Default organization: `https://dev.azure.com/ES-ECC-INNOVATION`
- Default project: `SOARPLUS`
- Parent relation must be verified on read-back before claiming success.
- Idempotency guard: checks if a child Task with the identical title and parent already exists; if found, refuses to create a duplicate and reports existing ID.

## Available script commands

All commands require `export AZURE_CONFIG_DIR=/tmp/soarplus-azure-cli` and valid `AZURE_DEVOPS_PAT`.

### 1. Dry run / check connection
```bash
python3 .agents/skills/ado-work-items/scripts/ado_cli.py check --parent 696
```

### 2. Create child Task
```bash
python3 .agents/skills/ado-work-items/scripts/ado_cli.py create-task \
  --parent 696 \
  --title "[CR-004] API: estado Quality forward-compatible" \
  --tags "cr-004; api" \
  --dry-run # omit --dry-run for actual creation
```

### 3. Read back work item
```bash
python3 .agents/skills/ado-work-items/scripts/ado_cli.py show --id 801
```

# Operational Envelope — api — start read-only Quality API (Q1)

Issued after explicit user request following pod recreation.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-api-6, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-api, path: /root/soarplus-api, branch: feature/696-sre-response-quality, expected_head: f34bf9c48ab05a845e37dac5263048c64cec1a3d}
objective: Start the audited read-only Quality API for the hybrid workflow on loopback port 8000.
acceptance_criteria:
  - Verify no listener/process on 8000 and persistent repo state unchanged before writes.
  - Install canonical orchestration `scripts/run_api_local_ui.py` to `/root/run_api_local_ui.py` and verify identical SHA256.
  - Start it in background with the repository venv, `GRANT_USER_ID` unset; persist PID and sanitized log in `/tmp`.
  - Verify PID alive; listener only on 127.0.0.1:8000; health 200; synthetic viewer/admin/noaccess matrix; `/user/me` and `/user/settings` 200 for local-admin with CORS origin exactly http://localhost:3000; Quality targets/metrics readable.
  - Confirm log shows discovery omitted/read-only guard and no unexpected blocked write during startup/smoke.
  - Do not use `run_api_local_quality.py`, `run_local.sh` or `run_api_local_granted.py`.
  - No source/state/config changes, commit, push, ADO, PR or deploy.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```
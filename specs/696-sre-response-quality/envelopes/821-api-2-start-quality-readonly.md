# Operational Envelope — API — start audited local Quality read-only API (Q2)

User explicitly requested full local stack restart after temporary `/tmp` runtime disappeared.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-api-12, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-api, path: /root/soarplus-api, branch: feature/696-sre-response-quality, expected_head: f34bf9c48ab05a845e37dac5263048c64cec1a3d}
objective: Start canonical audited read-only Quality API on 127.0.0.1:8000.
acceptance_criteria:
  - Verify no port/process 8000; install canonical run_api_local_ui.py to `/root/run_api_local_ui.py`; hashes identical.
  - Start with repository venv and `GRANT_USER_ID` unset; PID/log under `/tmp`.
  - Verify health 200, loopback listener, synthetic auth matrix, CORS exact localhost:3000, Quality targets/metrics and known judge_unavailable runs 200 after CR-004.
  - Log shows read-only guard/discovery omitted and no startup ERROR/Traceback.
  - Do not use normal/granted/old launcher; no repo/delivery changes, no DB write/direct command, no commit/push/PR/deploy.
```

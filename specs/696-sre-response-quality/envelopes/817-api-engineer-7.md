# Task Envelope — 817 — api-engineer — CR-001 tooling (E7)

Issued 2026-10-19 by the admiral. Immutable once sent.

Follow-up tooling envelope under CR-001 / Task #817: T032, user-requested and approved in the
admiral session on 2026-10-19 (recorded in the global tasks.md).

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: CHANGE
change_request: CR-001
feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality

assignment:
  ado_task: 817
  spec_tasks: [T032]

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Version the local quality integration tooling into the repository and update it to the amended
  R1–R6 surface, then regenerate and validate the Postman collection and environment against the
  read-only local API.

acceptance_criteria:
  - scripts/integration/quality_integration_check.py exists in the repo, based on /root/quality_integration_check.py, updated to R1-R6: new R2 (GET /quality/targets/{target}/evaluations, <=5 items desc tie-break eval_run_id, total = full-series count, first item == catalog latest, no limit/offset/order params), old 5-segment URL asserted 404, conditional 409 collision check (runs only if the catalog shows a cross-type name collision; otherwise reported as not-exercised), R6 (/quality/targets/history: gate 401/403/200/200, pagination by targets, deterministic (target_type,target) order, limit=501 -> 422, per-item history <=5 desc matching R2 for the same target), restored non-vacuous R3/R4 loop (fails loudly if no evaluation id was collected), R1 stable-order check by (target_type, target), FR-009 sweep kept on every 200 response.
  - scripts/integration/postman/build_quality_collection.py exists in the repo, based on /root/postman/build_quality_collection.py, generating the collection and environment with: R2 folder and gate rebuilt for the type-less URL and last-5 semantics, new R6 folder with its own gate and bounds requests, discovery folder updated, request counter fixed to count nested folders correctly, collection title updated to reference US 696 / Task 817 / CR-001.
  - The two generated JSONs (collection + environment) are committed under scripts/integration/postman/ and are the output of the committed generator (regenerate, do not hand-edit).
  - Validation run and recorded: start /root/run_api_local_quality.py (read-only guard against shared dev DocumentDB), run the updated quality_integration_check.py to completion with zero failed checks (document any check not exercisable on current data, e.g. the 409 collision), and run the generated collection logic equivalently (newman if available, otherwise document that the collection was validated via the script parity and manual spot-checks).
  - No write reaches DocumentDB: the read-only guard stays active for the whole validation; any guard trip aborts and is reported.
  - /root/quality_integration_check.py and /root/postman/* are NOT modified or deleted (out of repository scope; deprecated copies).
  - T032 marked [x] in the local tasks.md only after validation passed; IMPLEMENTATION-CHECKPOINT.md updated (tooling section: what moved into the repo, validation evidence, data-dependent checks not exercised).
  - Unit suite unaffected (no production code changes expected; if any src change proves necessary, return a blocker instead).

contracts:
  consumes:
    - name: quality-read-api (amended by CR-001)
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api
  provides: []

dependencies: []

constraints:
  - Follow the repository constitution and AGENTS.md; stage explicit paths only; never git add -A or git add .
  - Unrelated dirty/untracked files remain untouched (same inventory as E6).
  - Branch ahead of origin; do not push (see delivery).
  - Commit trailer: "Refs: #696 #817".
  - The local API runs against the SHARED dev DocumentDB: read-only operations only; keep AGENT_DISCOVERY_DB_FALLBACK=1 as per the runbook.

delivery:
  update_ado: true     # progress comment on Task #817 only; read back anything you report
  commit: true
  push: false
  create_pr: false
  deploy: false
```

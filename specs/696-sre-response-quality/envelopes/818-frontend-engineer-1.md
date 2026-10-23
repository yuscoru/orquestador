# Task Envelope — 818 — frontend-engineer — quality view (F1)

Issued 2026-10-19 by the admiral. Immutable once sent.

First envelope for soarplus-frontend-app1 in this feature: authorizes feature materialization
(T034) and delivers the whole approved frontend phase (T034–T038, gates 1–3 approved 2026-10-19).

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: FEATURE
feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality
  # frontend phase artifacts: spec-frontend.md, plan-frontend.md, tasks.md Phase 9

assignment:
  ado_task: 818
  spec_tasks: [T034, T035, T036, T037, T038]

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality   # create per T034 (pull main --ff-only first)

worker: frontend-engineer

objective: >
  Deliver the Quality view: /quality page with the catalog of evaluated targets (R1) and, on
  selection, the evolution of the two quality metrics (last 5 points, R2) with status and sample
  size, metric descriptors from R5, gated in the UI by is_admin || quality.view from /user/me,
  with the backend 403 as final authority.

acceptance_criteria:
  - T034: main updated with git pull --ff-only before branching (abort+blocker if not fast-forward); branch created; local specs/696-sre-response-quality/ projected from the frontend artifacts; npm ci from the lockfile; baseline npm run lint and npm run build recorded BEFORE changes.
  - T035: types mirror the OpenAPI of soarplus-api f34bf9c (status string|null, sample_sufficient boolean|null, MetricValue explicit-absence, {items,total}); UserDetails gains effective_capabilities: string[]; three api.ts functions via apiFetch only.
  - T036: page + components per plan §1/§2 with ALL states: empty catalog, 404 target, 409 (API Spanish detail shown), 403 no-access, load-more only when items.length < total, R2 total visible, legacy status null rendered "unknown (legacy)" with distinct chart marker, metric absence rendered as absence (never 0), labels/scale/polarity from R5 (no hardcoding).
  - T037: conditional nav entry + redirect-to-"/" without access (is_admin || effective_capabilities.includes("quality.view")); no credential field from /user/me read, stored or displayed.
  - T038: npm run lint and npm run build pass; manual validation checklist executed against the read-only local API with real dev data (catalog ordered+total; <=5 desc points; legacy point visible; absence != 0; 404 state; 403 state with no-access token; nav hidden without access) with per-item evidence in IMPLEMENTATION-CHECKPOINT.md; T034-T038 marked [x] in local tasks.md only after validation.
  - No new runtime dependency; no change outside the plan §2 touch list; no test framework introduced.

contracts:
  consumes:
    - name: quality-read-api (C-01, R1+R2+R5, as amended by CR-001+CR-002)
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api
      provider_state: pushed feature branch f34bf9c (user-accepted pre-merge dependency, Gate 2 D-F4 option 2)
    - name: quality.view (C-02) + GET /user/me effective_capabilities
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-02-quality-view-capability
  provides: []

dependencies:
  - repository: soarplus-api
    status: pushed-not-merged (f34bf9c on origin feature branch)
    reason: user explicitly accepted implementing against it (rework risk if api changes pre-merge)

constraints:
  - Follow the repository AGENTS.md and constitution; validation per repo convention (lint + build + manual, no test framework).
  - For the manual validation, the api repo provides the local read-only server (/root/run_api_local_quality.py); coordinate nothing: it is a local process, read-only guard required.
  - Untracked pre-existing files (.github/, .specify/, .vscode/, AGENTS.md) are NOT part of this assignment: do not commit them wholesale; stage explicit paths only; never git add -A or git add .
  - Commit trailer: "Refs: #696 #818".
  - If a criterion is unsatisfiable as written (e.g. no dev data visible, CORS, /user/me shape differs), return a blocker; do not improvise.

delivery:
  update_ado: true     # Task #818 only; read back anything you report
  commit: true
  push: false
  create_pr: false
  deploy: false
```

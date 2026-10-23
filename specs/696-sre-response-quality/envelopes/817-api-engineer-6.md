# Task Envelope — 817 — api-engineer — CR-001 (E6)

Issued 2026-10-19 by the admiral. Immutable once sent.

Change envelope: implements the approved Change Request CR-001 (delta gate 2026-10-19) on the
already-implemented feature 696. Single envelope for the whole CR (T027–T031).

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: CHANGE
change_request: CR-001   # specs/696-sre-response-quality/changes/CR-001.md

feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality

assignment:
  ado_task: 817
  spec_tasks: [T027, T028, T029, T030, T031]

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Apply the CR-001 delta to the quality read contract: (D1) the single quality predicate becomes
  schema_version 4 + mode offline_log + both headline metrics scored, used by every quality query
  and count; (D2) the per-target history returns at most the last 5 scored points by timestamp
  descending (tie-break eval_run_id), with no paging parameters; (D3) the history path becomes
  /quality/targets/{target}/evaluations with a 409 (Spanish detail) when matching documents span
  more than one target_type; (D4) a new route GET /quality/targets/history returns all targets
  paginated by target, each with its last-5 scored history, same point shape and gate as the rest.

acceptance_criteria:
  - Re-project only the CR-001 delta into the local specs/696-sre-response-quality artifacts (spec.md, plan.md, tasks.md), preserving completed tasks and original ids; add T027-T031 as in the global tasks.md. Do not regenerate artifacts.
  - The predicate change (T027) is covered by unit tests written first: inclusion of scored v4/offline_log points regardless of checkpoint/status/rescore/validation markers; exclusion of unscored, wrong-schema and wrong-mode documents; absent-vs-null handled for the metric fields.
  - R2 (T028): GET /quality/targets/{target}/evaluations returns at most 5 items, timestamp desc, tie-break eval_run_id; envelope {items, total} with total = the target's scored-point count; 404 on zero scored points; 409 with Spanish detail when matches span more than one target_type; no limit/offset/order parameters remain; old path /quality/targets/{target_type}/{target}/evaluations no longer exists.
  - R6 (T029): GET /quality/targets/history paginated by targets with documented default and hard maximum, deterministic order by (target_type, target), no target_type/eval_profile filters; item {target_type, target, eval_profile, history: last-5 EvaluationPoint desc}; gated by quality.view via authorize_capability_or_admin like the other routes.
  - Catalog, detail and cases use the same redefined predicate; catalog counts and latest reflect it.
  - T030: contract test updated to the amended surface (paths R1-R6, no FR-009 field name in any response schema including R6); gate tests cover the new/changed routes; README/route documentation updated.
  - T031: complete soarplus-api unit suite run and recorded, distinguishing pre-existing baseline failures (test_usage x2, test_llm_providers_manage_own_capability x3) from new ones; IMPLEMENTATION-CHECKPOINT.md updated with the CR-001 delta, evidence, and what was not verified live.
  - T027-T031 marked complete in the local tasks.md only if their validation passed.

contracts:
  consumes: []
  provides:
    - name: quality-read-api (amended by CR-001)
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api

dependencies: []

constraints:
  - Follow the repository constitution, AGENTS.md and scoped instructions; tests first.
  - The working tree contains uncommitted changes and untracked files NOT part of this assignment (modified .gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py; untracked .agents/, .env, .github/, .specify/, .vscode/, AGENTS.md, scripts/ extras). Do not modify, revert, stage or commit them. Stage explicit paths only; never git add -A or git add .
  - HEAD d8faac3 is 7 commits ahead of origin. Do not push (see delivery).
  - Do not run /speckit.specify, /speckit.plan or /speckit.tasks. Apply the delta from source.artifacts.
  - Commit trailer: "Refs: #696 #817".
  - If a criterion is unsatisfiable as written, return a blocker; do not loosen it locally.

delivery:
  update_ado: true     # progress on Task #817 only; read back anything you report
  commit: true
  push: false
  create_pr: false
  deploy: false
```

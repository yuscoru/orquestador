# Task Envelope — 801 — api-engineer — slice 2 of 5 (E2) — retry 1

Issued 2026-10-15 by the admiral. Immutable once sent.

Retry note: the first E2 invocation (envelopes/801-api-engineer-2.md) returned no Task Result and no Blocker Result. See log.md. The assignment is unchanged; only the constraints below add the observed state.

Slice note: second of five sequential envelopes for Task #801. Local feature directory already materialized by
E1 (commit d2b4df9); do not re-materialize.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT

feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality

assignment:
  ado_task: 801
  spec_tasks:
    - T007
    - T008
    - T009
    - T010
    - T011

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Deliver the foundation of the quality read contract: typed response models for every type in plan.md
  section 3, a data-access layer over a2a_tasks.agent_eval_results that embeds one single valid-point
  predicate and allow-list projections, verification of the per-rubric explanation-availability projection
  path, and a controller module with the shared document-to-DTO mapping and strict input validators. No
  route is exposed in this envelope.

acceptance_criteria:
  - Tests for T007 are written first and fail before the implementation exists.
  - The valid-point predicate is defined once in the data-access layer and excludes - schema_version other than 4, mode other than offline_log, uncommitted windows, monitoring status outside the five contract statuses (measured, low_sample, no_activity, no_eligible_cases, evidence_incomplete; therefore judge_unavailable never qualifies), documents with a rescore marker, documents with a validation marker; rescore and validation markers are handled both as absent keys and as explicit nulls.
  - Every projection is an inclusion allow-list built from the exposure rules of plan.md section 3; none of the FR-009 fields can be produced by it (judge-generated text, construction trace, published-deliverable provenance, tracking/telemetry, root task id lists, execution trees, evaluator fingerprint, source reference, passed, thresholds, invocations, baseline comparability). This is asserted by tests.
  - Pydantic response models for MetricValue, EvaluationPoint, catalog item, Distribution, rubric result, Case, evaluation detail, metric descriptor and the items/total envelopes exist in api/utils/models.py, with no inline models elsewhere; metrics is a typed object with one property per metric id, both always present; an unscored metric is value null, never 0.
  - DatabaseService exposes an agent_eval_results collection attribute on the a2a_tasks database and read-only query methods (history page + count, catalog source, detail, cases source). The API creates no index on this collection and never writes to it.
  - T010 outcome is recorded - the exact nested path of the per-rubric explanation-available flag in the persisted document was verified against the writer model and fixtures in soarplus-agentics (read-only) and it was confirmed whether it can be projected as an inclusion path without the sibling judge text.
  - control_quality controller module exists with the shared mapping (absent metric -> value null; unavailable from presence of the key in the unavailable-metrics map only, never the free text) and validators (target_type, eval_profile and order as enums, target as a conservative pattern, eval_run_id as 32 lowercase hex). User input is only ever used as an equality literal. Blocking pymongo calls are wrapped with asyncio.to_thread.
  - No route is registered, api/api.py is not changed, GET /db/collections and GET /db/collections/{collection_name} are not modified, and no capability gate is exercised yet.
  - The new tests pass, the RBAC suites still pass, and the full unit suite shows no failure beyond the 5 recorded baseline failures (test_usage x2, test_llm_providers_manage_own_capability x3); any other failure is yours to fix.
  - T007-T011 are marked complete in the local tasks.md only if their validation passed and the local IMPLEMENTATION-CHECKPOINT.md is updated with current reality, including the T010 outcome.

contracts:
  consumes:
    - name: agent_eval_results document v4
      provider: soarplus-agentics
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-03-agent-eval-result-document
  provides:
    - name: quality-read-api
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api

dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Document shape is stable; read-only inspection of its writer model and fixtures is needed for T010.

constraints:
  - Follow the repository constitution, AGENTS.md, .github/copilot-instructions.md and the scoped python-fastapi and testing instructions; tests first.
  - Same working-tree rules as E1 - the pre-existing uncommitted modifications and untracked files are not part of this assignment; do not modify, revert, stage or commit them; stage explicit paths only; never git add -A or git add .
  - RESUMPTION - a previous attempt of this same assignment ended without a result and left uncommitted work in the tree: modified api/AWS/documentdb.py and api/utils/models.py, and new api/controllers/control_quality.py, tests/test_quality_data_access.py and tests/test_quality_models_and_controller.py. These five paths are in scope for this assignment. Do not trust them as finished: inspect them, run the tests, and decide for yourself what is sound. Keep what satisfies the acceptance criteria, fix or replace the rest. Do not discard work silently; say in the result what you kept, changed or removed. local tasks.md and IMPLEMENTATION-CHECKPOINT.md were not updated by that attempt.
  - The other pre-existing modified and untracked files (.gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py, .agents/, .env.local.example, .github/, .specify/ except feature.json, .vscode/, AGENTS.md, scripts/run_local.sh) are still NOT part of this assignment.
  - Work in small verifiable steps and commit as soon as the assigned tasks validate, so that an interruption cannot again leave only uncommitted work. Always finish by returning a Task Result or a Blocker Result.
  - Do not push. HEAD is already ahead of its remote.
  - T010 is a hard stop. If the explanation-available flag cannot be projected without the sibling judge text, or the nested path cannot be established with evidence, stop and return a Blocker Result addressed to the captain (blocker type ARCHITECTURE_DECISION_REQUIRED or CONTRACT_CHANGE_REQUIRED as appropriate). Do not widen the projection, do not drop the indicator silently, and do not guess the path.
  - Do not use the MTA controller or the /agents/tasks code as a template for async behaviour or paging bounds.
  - Do not modify soarplus-agentics or any other repository; reading soarplus-agentics for T010 is permitted.
  - Do not mark any task outside T007-T011 as complete.
  - If the planned approach is unworkable, return a blocker for the captain; do not rewrite the plan locally.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in code, commits, ADO comments or the result.

validation_expectations:
  - Focused unit tests for T007 and for the mapping and validators of T011 pass.
  - Allow-list assertions are executed by tests, not only by inspection.
  - RBAC suites pass; full suite compared against the recorded baseline.
  - Report any acceptance criterion that could not be verified, including anything that needs a live DocumentDB.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```

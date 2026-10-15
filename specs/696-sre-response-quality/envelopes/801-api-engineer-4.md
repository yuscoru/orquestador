# Task Envelope — 801 — api-engineer — slice 4 of 5 (E4)

Issued 2026-10-15 by the admiral. Immutable once sent.

Slice note: fourth of five sequential envelopes for Task #801. E1 (d2b4df9), E2 (bad615b) and E3 (b7d2510) are
completed. The capability, models, data-access layer, controller module, router and routes R1 and R2 already
exist, as does the verified path of the per-rubric explanation-availability flag (T010).

Format note: the E3 result was returned as free-form markdown. This envelope REQUIRES the canonical structure of
protocols/task-result.md (or protocols/blocker-result.md).

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
    - T017
    - T018
    - T019
    - T020
    - T021

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Complete the route surface of the quality read contract as designed in plan.md section 3 and section 7.1: R3,
  the detail of one evaluation without its cases; R4, the paginated evaluated cases of one evaluation; and R5,
  the static metric descriptors. All behind the quality.view gate, none exposing judge-generated text.

acceptance_criteria:
  - Tests for T017 (R3), T018 (R4) and T019 (R5) are written first and fail before the implementation exists.
  - R3 GET /quality/evaluations/{eval_run_id} returns the evaluation point fields plus target_type, target, distributions per metric id (n, mean, stdev, sem, min, max, p10, p50, p90, or null when the metric has no distribution), rubrics as a list of rubric_id and fulfilment_rate, and case_count; eval_run_id is 32 lowercase hex (malformed -> 422); a document that is not a valid series point -> 404 with a Spanish detail message.
  - R4 GET /quality/evaluations/{eval_run_id}/cases returns an items/total envelope with limit default 50 bounded 1-200 and offset >= 0 (outside bounds -> 422); each Case has eval_id, metrics per metric id (float or null), rubrics as a list of rubric_id, score 0 or 1 and explanation_available, unscored_rubrics, and unavailable_metrics as a list of metric_id and reason (evidence_unavailable or judge_unavailable). Cases are merged by eval_id from the per-case scores and the per-case diagnostics, a case present in only one source still renders, and paging is applied after the merge with a deterministic order. Unknown or not-valid evaluation -> 404.
  - explanation_available is derived from the verified path of the per-rubric flag only; no field carrying judge-generated text (sentences, rationales, supporting or contradicting excerpts, any judge_diagnostics subtree beyond that flag) is projected, fetched into a response or returned. Tests assert this with a document carrying sentinel text in every forbidden field.
  - R5 GET /quality/metrics returns static descriptors for hallucinations_v1 and rubric_based_final_response_quality_v1 with metric_id, label, description, scale_min 0, scale_max 1 and higher_is_better true for both; the label of hallucinations_v1 is exactly "Fidelidad a la evidencia"; R5 performs no database access (asserted by a test).
  - All three routes declare response_model, are added to the existing quality router, are gated by the module-level quality_view_authorize dependency (authorize_capability_or_admin on quality.view), and no route in the quality router exists without the gate. Tests assert the dependency by introspection. require_capability is not used.
  - User input is validated and used only as an equality literal; operator-injection strings are rejected (422) or treated as literals; covered by tests.
  - GET /db/collections and GET /db/collections/{collection_name} are not modified. The API creates no index on agent_eval_results and never writes to it. api/api.py needs no new registration (the router is already registered); do not change it unless strictly necessary and say why.
  - The new tests pass, the RBAC suites pass, and the full unit suite shows no failure beyond the 5 recorded baseline failures (test_usage x2, test_llm_providers_manage_own_capability x3); any other failure is yours to fix.
  - T017-T021 are marked complete in the local tasks.md only if their validation passed; IMPLEMENTATION-CHECKPOINT.md is updated with current reality and what remains unverified against a live DocumentDB.
  - The Task Result uses the canonical structure of protocols/task-result.md, including assignment, acceptance_criteria with PASS/FAIL/NOT_VERIFIED and evidence, contracts, validation, repository_state, ado, git, pull_request, deployment, remaining_work, risks and warnings.

contracts:
  consumes:
    - name: agent_eval_results document v4
      provider: soarplus-agentics
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-03-agent-eval-result-document
    - name: quality.view
      provider: soarplus-api
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-02-quality-view-capability
  provides:
    - name: quality-read-api
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api

dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Document shape is stable; no change needed there.

constraints:
  - Follow the repository constitution, AGENTS.md, .github/copilot-instructions.md and the scoped python-fastapi and testing instructions; tests first.
  - The pre-existing uncommitted modifications and untracked files (.gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py, .agents/, .env.local.example, .github/, .specify/ except feature.json, .vscode/, AGENTS.md, scripts/run_local.sh) are not part of this assignment; do not modify, revert, stage or commit them; stage explicit paths only; never git add -A or git add .
  - Work in small verifiable steps and commit as soon as the assigned tasks validate, so that an interruption cannot leave only uncommitted work. Always finish by returning a Task Result or a Blocker Result as your final message, in canonical structure; if running short of room, stop at a validated state, commit it and return a PARTIAL result listing the remaining work precisely.
  - Do not push. Do not touch any other repository. Do not mark any task outside T017-T021 as complete.
  - Do not start T022-T026 (contract test over the router, cross-cutting tests, documentation, final full-suite run, final checkpoint); they belong to E5.
  - Do not use the MTA controller or the /agents/tasks code as a template for async behaviour or paging bounds; use Query(ge, le).
  - If the planned approach is unworkable or a task is not satisfiable as written, return a blocker for the captain; do not rewrite the plan locally.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in code, commits, ADO comments or the result. When commenting on Azure DevOps, use the Azure DevOps integration for project SOARPLUS and Task #801 only, and confirm the comment by reading it back.

validation_expectations:
  - Focused unit tests for T017, T018 and T019 pass; route gate and bounds covered by tests.
  - The "no judge text" guarantee for R3 and R4 covered by sentinel-based tests.
  - RBAC suites pass; full suite compared against the recorded baseline.
  - Report any acceptance criterion that could not be verified, including anything that needs a live DocumentDB.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```

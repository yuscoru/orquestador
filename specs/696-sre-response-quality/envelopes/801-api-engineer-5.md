# Task Envelope — 801 — api-engineer — slice 5 of 5 (E5)

Issued 2026-10-15 by the admiral. Immutable once sent.

Slice note: last of five sequential envelopes for Task #801. E1 (d2b4df9), E2 (bad615b), E3 (b7d2510) and E4 (84bfd0c)
are completed. The full route surface (R1-R5), the capability, models, data access and controller exist.

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
    - T022
    - T023
    - T024
    - T025
    - T026

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Close the soarplus-api work of Task #801: verify the published contract through the generated OpenAPI schema of
  the quality router, cover the cross-cutting access rules with tests, document the new routes and capability,
  run the complete unit suite and leave the final IMPLEMENTATION-CHECKPOINT.md with the cassdk impact assessment
  and an honest statement of what is not verified.

acceptance_criteria:
  - T022 - a contract test builds a FastAPI app containing only the quality router (FastAPI() + include_router, stubbing as the existing route tests do) and asserts on app.openapi(): the five paths and their methods; the parameters with their bounds and defaults (limit, offset, order, filters); response_model schemas present for every route; the metrics object lists exactly the two metric ids; and that NO response schema contains any FR-009 field name or any judge-text field name (sentence, rationale, supporting_excerpt, contradicting_excerpt, judge_diagnostics, construction_trace, published_deliverable, tracking, fingerprint, source_ref, passed, thresholds, invocations, is_baseline_comparable, root_task_ids, execution). If this approach needs heavy stubbing that cannot be made reliable, return a blocker instead of skipping the test.
  - T023 - cross-cutting access tests: every route of the quality router requires the gate; an unauthenticated caller is rejected; a caller without quality.view is rejected with 403; a caller whose role holds quality.view is accepted; an administrator whose role document does NOT list quality.view is accepted (admin bypass); GET /quality/metrics is gated too. Existing authorize_capability_or_admin suites may be reused where they already cover a case, but the matrix must be demonstrated for the quality routes.
  - T024 - documentation of the five routes, the quality.view capability (including that it is granted by default to the predefined user role by a one-shot startup backfill, and that users on custom roles do not receive it by default) and the fact that this phase does not change GET /db/collections*, placed where this repository documents routes and capabilities (README or the location its conventions prescribe; state which).
  - T025 - the complete unit suite is run and the result recorded: counts, and the failing test ids compared with the 5 recorded baseline failures (test_usage x2, test_llm_providers_manage_own_capability x3). In addition, determine whether those 5 failures pre-date the feature and the user's uncommitted edits: export the pre-feature commit 580a532 to a temporary directory WITHOUT touching the working tree or git state (for example git archive 580a532 | tar -x -C <tmpdir>), run only those failing tests there, report whether they fail identically, and delete the temporary directory afterwards. Do not use git stash, git checkout of files, git worktree or any operation that alters the user's working tree.
  - T026 - IMPLEMENTATION-CHECKPOINT.md is finalized with - what was implemented per envelope; the catalog strategy (controller-side reduction) and its stated trigger for revisiting; the outcome of T010; the local decisions taken where the plan was silent; the cassdk impact assessment (YES - additive client addition; list the new routes and the capability; state that cassdk is not present in this environment and was not inspected; and that the new routes do not change any existing client contract); the accepted risk that GET /db/collections* still lets any authenticated user read agent_eval_results including judge text; and everything not verified (live DocumentDB behaviour of the predicate, sort and projection through arrays; writer indexes; Python 3.13 runtime; custom roles).
  - No behavioural change to R1-R5 is made unless a test in T022/T023 reveals a defect; any such fix is minimal, covered by a test and reported explicitly.
  - GET /db/collections and GET /db/collections/{collection_name} are not modified. The API creates no index on agent_eval_results and never writes to it.
  - T022-T026 are marked complete in the local tasks.md only if their validation passed. All of T003-T026 are then accounted for in the local tasks.md.
  - The Task Result uses the canonical structure of protocols/task-result.md, with acceptance_criteria PASS/FAIL/NOT_VERIFIED and evidence for each criterion.

contracts:
  consumes:
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
  - Follow the repository constitution, AGENTS.md, .github/copilot-instructions.md and the scoped python-fastapi and testing instructions; tests first where behaviour is added.
  - The pre-existing uncommitted modifications and untracked files (.gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py, .agents/, .env.local.example, .github/, .specify/ except feature.json, .vscode/, AGENTS.md, scripts/run_local.sh) are not part of this assignment; do not modify, revert, stage or commit them; stage explicit paths only; never git add -A or git add .
  - Work in small verifiable steps and commit as soon as the assigned tasks validate, so that an interruption cannot leave only uncommitted work. Always finish by returning a Task Result or a Blocker Result as your final message, in canonical structure; if running short of room, stop at a validated state, commit it and return a PARTIAL result listing the remaining work precisely.
  - Do not push. Do not create a pull request. Do not touch any other repository. Do not mark any task outside T022-T026 as complete, and do not close or change the state of ADO Task #801 (it stays Active until merge).
  - If the planned approach is unworkable or a task is not satisfiable as written, return a blocker for the captain; do not rewrite the plan locally.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in code, commits, ADO comments or the result. When commenting on Azure DevOps, use the Azure DevOps integration for project SOARPLUS and Task #801 only, and confirm the comment by reading it back.

validation_expectations:
  - Contract test (T022) and cross-cutting tests (T023) pass.
  - Complete unit suite run (T025) with the comparison against the recorded baseline and the isolation check described above.
  - Report any acceptance criterion that could not be verified, including everything that needs a live DocumentDB.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```

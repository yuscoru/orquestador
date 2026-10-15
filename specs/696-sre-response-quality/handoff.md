# Handoff to Admiral — 696-sre-response-quality (phase 1: quality read contract in soarplus-api)

**Status**: Ready — spec (Gate 1), plan (Gate 2) and tasks (Gate 3) approved by the user on 2026-10-15,
including the post-gate amendment that withdrew the debug-route closure.

Global artifacts (read-only for workers): `/root/soarplus-dev-orchestration/specs/696-sre-response-quality/`
→ [spec.md](spec.md), [plan.md](plan.md) (the section 7.1 is the `soarplus-api` plan), [tasks.md](tasks.md),
[contracts.md](contracts.md).

```yaml
feature:
  ado_user_story: 696
  slug: sre-response-quality

repositories:
  - name: soarplus-api
    affected: true
    worker: api-engineer
    path: /root/soarplus-api
    branch: feature/696-sre-response-quality   # already checked out; no specs/ directory exists yet in this repo
    objective: >
      Publish a read-only REST contract over a2a_tasks.agent_eval_results (catalog of evaluated targets,
      paginated history per target, detail of one evaluation, paginated cases of one evaluation, static
      metric descriptors), behind a new capability quality.view granted by default to the predefined user
      role (admin by bypass), exposing only an allow-list of fields. Materialize the local specs from the
      global artifacts first, then implement with tests first.
    spec_tasks: [T003, T004, T005, T006, T007, T008, T009, T010, T011, T012, T013, T014, T015, T016,
                 T017, T018, T019, T020, T021, T022, T023, T024, T025, T026]
    ado_task: 801   # created 2026-10-15 under US 696, state Active (confirmed by reading it back)
    withdrawn_tasks: [T001, T002]   # must not be projected as work; ids are reserved and never reused
    acceptance_criteria:
      - Routes R1-R5 under /quality exist with response_model, bounded paging and the quality.view gate.
      - Only valid series points are ever returned (schema 4, offline_log, committed, status in the five
        contract statuses, not rescore, not validation); runs with judge_unavailable never appear.
      - No response contains judge-generated text or any other FR-009 field; exposure is an allow-list
        projection, verified by tests and by a contract test over the router's OpenAPI.
      - An unscored metric is returned as null (never 0); metrics is a typed object with both metric ids.
      - quality.view is in the capability catalog, in the user seed for new deployments, and backfilled once
        (flagged, idempotent, run last at startup) for existing deployments; admins are never locked out;
        require_capability is not used for this gate.
      - Orchestrators are selected via eval_profile; no third target_type and no derived "kind" field.
      - The API creates no index on agent_eval_results and never writes to it.
      - GET /db/collections and GET /db/collections/{collection_name} are NOT modified.
      - IMPLEMENTATION-CHECKPOINT.md records the catalog strategy, the T010 outcome, the cassdk impact
        assessment, what was not verified, and the accepted exposure of the generic routes.
    contracts:
      provides:
        - {name: quality-read-api, type: REST, consumers: [soarplus-frontend-app1, cassdk], reference: contracts.md C-01}
        - {name: quality.view, type: capability, consumers: [soarplus-frontend-app1, cassdk], reference: contracts.md C-02}
      consumes:
        - {name: agent_eval_results document v4, provider: soarplus-agentics, reference: contracts.md C-03}
    dependencies:
      - repository: soarplus-agentics
        type: data contract
        status: ready
        reason: Document shape is stable and read-only for this feature; no change required there.
    constraints:
      - Repository constitution, AGENTS.md, copilot-instructions and scoped instructions prevail (TDD,
        unittest, no inline models, layering, no blocking I/O in async code).
      - Tests are written first and must fail before the implementation exists.
      - Do not modify soarplus-agentics, soarplus-frontend-app1 or any other repository.
      - Do not use the MTA controller or /agents/tasks as a template for paging bounds or async behaviour.
      - T010 is a hard stop: if rationale_available cannot be projected without the sibling text, return a
        blocker to the Captain; do not widen the projection or drop the indicator silently.
      - T022: if the isolated-router OpenAPI test needs heavy stubbing, return a blocker instead of skipping it.
    validation_expectations:
      - Unit tests per tasks.md, no network, AWS mocked per testing.instructions.md.
      - Contract test over the new router (T022).
      - Existing RBAC suites (test_rbac_capabilities.py, test_predefined_roles_seeding.py) still pass.
      - Full soarplus-api unit suite result recorded (T025).
      - Real-data smoke on dev is NOT performable by the worker and must be reported as unverified.

cross_repo_contracts:
  - {id: C-01, name: quality-read-api, provider: soarplus-api, consumers: [soarplus-frontend-app1, cassdk]}
  - {id: C-02, name: quality.view, provider: soarplus-api, consumers: [soarplus-frontend-app1, cassdk]}
  - {id: C-03, name: agent_eval_results v4, provider: soarplus-agentics, consumers: [soarplus-api]}

cross_repo_risks:
  - {severity: HIGH, ref: "plan R-1", description: >
      Accepted by the user: GET /db/collections/{collection_name} still lets any authenticated user read
      agent_eval_results including unredacted judge prose. Not mitigated by this feature. A separate
      security task is recommended.}
  - {severity: MEDIUM, ref: "plan R-3/R-4/R-6", description: >
      Not verifiable by workers (no network): real document shape (absent vs null markers), DocumentDB
      aggregation support, and existence of the writer's indexes. Needs a user/ops check on dev.}
  - {severity: MEDIUM, ref: "plan R-5", description: >
      Projecting rationale_available alone may not be possible (task T010). Possible blocker.}
  - {severity: MEDIUM, ref: "plan R-7 / O-1", description: >
      Users on custom roles do not get quality.view by default. Accepted.}
  - {severity: INFO, ref: "plan R-12", description: >
      Names of private playbooks that are evaluated may appear in the catalog. Accepted by the user.}

unresolved_orchestration_requirements:
  - requirement: cassdk client addition and version bump for the new routes (additive)
    status: unresolved
    reason: cassdk has no registered worker and the repository is not present in this environment.
  - requirement: ADO Task for this work
    status: resolved
    reason: >
      Task #801 ("T-Q · API: contrato de lectura de evolución de calidad por target") exists under US 696,
      state Active. Commit trailer: "Refs: #696 #801".
  - requirement: user/ops checks (custom roles via GET /rbac/roles, writer index existence, smoke on dev)
    status: unresolved
    reason: Need live access the registered workers do not have.
  - requirement: frontend view and any soarplus-kubernetes follow-up
    status: out of scope for this phase
    reason: Later phase; no registered worker for soarplus-kubernetes.

recommended_execution_order:
  - step: 0
    action: ADO Task #801 created and Active. Done; use assignment.ado_task 801 in every envelope.
  - step: 1
    envelope: E1
    worker: api-engineer
    spec_tasks: [T003, T004, T005, T006]
    note: RBAC capability and default grant. Independent of the data layer. First envelope must also
          materialize the local specs (branch already exists).
  - step: 2
    envelope: E2
    worker: api-engineer
    spec_tasks: [T007, T008, T009, T010, T011]
    note: Foundation. T010 may return a blocker to the Captain.
  - step: 3
    envelope: E3
    worker: api-engineer
    spec_tasks: [T012, T013, T014, T015, T016]
    note: Catalog and history. Deliverable MVP of the evolution view together with E1 and E2.
  - step: 4
    envelope: E4
    worker: api-engineer
    spec_tasks: [T017, T018, T019, T020, T021]
    note: Detail, cases, metric descriptors.
  - step: 5
    envelope: E5
    worker: api-engineer
    spec_tasks: [T022, T023, T024, T025, T026]
    note: Contract test, docs, full suite, checkpoint with cassdk impact assessment.
  - step: 6
    action: User/ops checks and smoke on dev; Admiral routes the cassdk requirement.
  - step: 7
    action: Gate 4 (delivery) before any push, PR or deploy.

execution_note: >
  The grouping into envelopes E1-E5 is a recommendation. The Admiral may merge them or use one envelope for
  all tasks, provided the order of tasks.md dependencies is respected and every spec_tasks id is preserved.
```

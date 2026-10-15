# Tasks: Evolución de calidad por target — contrato de lectura en soarplus-api (fase 1)

**Input**: [spec.md](spec.md) (approved Gate 1), [plan.md](plan.md) (approved Gate 2), [contracts.md](contracts.md)

**Status**: Approved at Gate 3

> Gate: approved by user on 2026-10-15. Approved with T001 and T002 withdrawn (spec C2 amendment).

**Numbering authority**: this file. Ids are never renumbered downstream. The `soarplus-api` projection of
`tasks.md` preserves them.

**ADO Task**: #801 ("T-Q · API: contrato de lectura de evolución de calidad por target"), child of US #696,
state Active. Commits use `Refs: #696 #801`.

**Worker**: every task below is executed by `api-engineer` in `/root/soarplus-api`. Paths are relative to
that repository.

**Tests**: mandatory and written first (repository TDD rule). Test tasks precede the implementation they
cover and must fail before it exists.

## Format: `[ID] [P?] [Story] [worker] Description`

- **[P]**: can run in parallel (different files, no dependency on an unfinished task)
- **[Story]**: US1 catalog · US2 history · US3 detail · US4 access and data exposure

---

## Phase 1 — WITHDRAWN (generic collection-read routes)

T001 and T002 are withdrawn by the user on 2026-10-15 (spec C2). The ids are **kept and not reused** so that
references in conversation and artifacts stay valid. Nothing in this repository changes for these routes.

- [~] T001 *(withdrawn)* Test that the debug GET routes require admin.
- [~] T002 *(withdrawn)* Switch the debug GET routes to `admin_authenticate`.

**Accepted risk**: `agent_eval_results`, including judge prose, remains readable by any authenticated user
through `GET /db/collections/{collection_name}`. Recommended as a separate security task.

---

## Phase 2 — Capability and default grant (US4, FR-010)

**Goal**: `quality.view` exists, is granted to the `user` role on new and existing deployments, and admins
are never locked out.

- [ ] T003 [P] [US4] [api-engineer] Write tests (new file under `tests/`, pattern of `tests/test_sre_eval_capability.py` and `tests/test_llm_config_override_agent_pin_backfill.py`): `quality.view` is in `CAPABILITIES`; it is in the predefined `user` seed; the new backfill is flagged, idempotent (second run is a no-op) and does not override a role from which an admin removed the capability; the backfill is invoked **last** in the `DatabaseService.__init__` startup block.
- [ ] T004 [US4] [api-engineer] Add capability `quality.view` to `api/rbac_capabilities.py` and add its id to the `user` baseline tuple used by `ensure_predefined_roles_seeded` in `api/AWS/documentdb.py`. Depends on T003.
- [ ] T005 [US4] [api-engineer] Add `ensure_quality_view_capability_backfilled()` to `api/AWS/documentdb.py` following the one-shot flagged pattern of `ensure_llm_config_override_agent_pin_capability_backfilled`, and call it **last** in the startup `try` block. Depends on T004.
- [ ] T006 [US4] [api-engineer] Run `tests/test_rbac_capabilities.py` and `tests/test_predefined_roles_seeding.py` and fix any fallout caused by the catalog change. Depends on T005.

**Checkpoint**: T003 and T006 green.

---

## Phase 3 — Foundation: models, data access, shared mapping (blocks US1–US3)

**Goal**: one valid-point predicate, allow-list projections, typed response models.

- [ ] T007 [P] [US4] [api-engineer] Write tests for the data-access layer and the predicate: documents that are rescore, validation, uncommitted, `judge_unavailable`, `schema_version` ≠ 4 or `mode` ≠ `offline_log` are excluded; `rescore`/`validation` markers handled both **absent** and **explicit null**; the projections contain **none** of the FR-009 fields (judge text, construction trace, published deliverable, tracking, root task ids, execution trees, fingerprint, source reference, `passed`, `thresholds`, `invocations`, baseline comparability) and use inclusion paths only.
- [ ] T008 [P] [US4] [api-engineer] Add Pydantic response models for every type in plan.md §3 to `api/utils/models.py`: `MetricValue`, `EvaluationPoint`, catalog item, `Distribution`, rubric result, `Case`, detail, metric descriptor, and the `{items,total}` envelopes. No inline models in routes. `metrics` is a typed object with one property per metric id; both always present.
- [ ] T009 [US4] [api-engineer] In `api/AWS/documentdb.py` add the `agent_eval_results_collection` attribute (database `a2a_tasks`) and read-only methods embedding the single valid-point predicate and the allow-list projections: history page + count, catalog source, detail, cases source. Create **no** index on this collection. Depends on T007.
- [ ] T010 [US4] [api-engineer] Verify the exact nested path of the per-rubric `rationale_available` flag in the writer model and fixtures (`/root/soarplus-agentics/tools/sre-response-quality/sre_eval/agent_eval_result.py`, `judge_diagnostics.py`, tests) and confirm it can be projected as an inclusion path **without** the sibling `rationale` text. If it cannot, **stop and return a blocker to the Captain**; do not widen the projection and do not drop the indicator silently. Depends on T009.
- [ ] T011 [US4] [api-engineer] Create `api/controllers/control_quality.py` with shared document→DTO mapping (absent metric → `value: null`; `unavailable` from `summary.unavailable_metrics` key presence only, never the free text) and strict input validators (`target_type` and `eval_profile` enums, `order` enum, `target` conservative pattern, `eval_run_id` 32-hex). User input is only ever an equality literal. Blocking pymongo calls go through `asyncio.to_thread`. Depends on T008, T009.

**Checkpoint**: T007 green; T010 resolved (or blocker returned).

---

## Phase 4 — US1: catalog of evaluated targets (P1) 🎯

**Goal**: R1 `GET /quality/targets`.

**Independent test**: with mixed seeded documents each target appears once with its latest valid point;
targets whose documents are all invalid do not appear.

- [ ] T012 [P] [US1] [api-engineer] Write controller and route tests for R1: one row per `(target_type, target)`; `eval_profile` and `latest` from the most recent valid point; `evaluations` counts valid points only; filters `target_type` and `eval_profile`; order by `target_type`, `target`; bounds `limit` 1–500 default 100, `offset` ≥ 0 (422 outside); route declares the `quality.view` gate; operator-injection strings are literals or rejected.
- [ ] T013 [US1] [api-engineer] Implement the catalog in `api/controllers/control_quality.py` and its data method. Preferred: aggregation (valid points → latest per key + count). If the dev DocumentDB does not support it, use the fallback (`distinct` per `target_type` + one indexed query per target). **State in the checkpoint which was used and why.** Depends on T011, T012.
- [ ] T014 [US1] [api-engineer] Create `api/routes/quality.py` (prefix `/quality`, tag `Quality`, `response_model` on every route, gate `authorize_capability_or_admin(controller, "quality.view")` defined once at module level) with R1; register the router and the tag in `api/api.py`. Depends on T013.

**Checkpoint**: T012 green.

---

## Phase 5 — US2: history of one target (P1) 🎯

**Goal**: R2 `GET /quality/targets/{target_type}/{target}/evaluations`.

**Independent test**: a seeded target returns ordered, bounded pages with no invalid points; an unknown
target returns 404.

- [ ] T015 [P] [US2] [api-engineer] Write tests for R2: order by `timestamp` then `eval_run_id` (deterministic with equal timestamps) for `desc` and `asc`; bounded pages (`limit` 1–200 default 50, `offset` ≥ 0, else 422); `total` matches; points carry both metrics with explicit `null` when unscored, `n`, `status`, `window`, `evaluator` (profile, profile version, judge model); two points with different profile version or judge model are distinguishable; zero valid points → 404 in Spanish; gate declared.
- [ ] T016 [US2] [api-engineer] Implement R2 in `api/controllers/control_quality.py` and add the route to `api/routes/quality.py`. Depends on T011, T014, T015.

**Checkpoint**: T015 green. US1 + US2 together are the deliverable MVP of the evolution view.

---

## Phase 6 — US3: detail, cases, metric descriptors (P2)

**Goal**: R3, R4, R5.

**Independent test**: the detail of a seeded evaluation carries distributions, per-rubric rates and
`case_count`; the cases route pages the evaluated cases; none exposes judge text.

- [ ] T017 [P] [US3] [api-engineer] Write tests for R3: header + `distributions` per metric (`n, mean, stdev, sem, min, max, p10, p50, p90`, `null` when the metric has no distribution), `rubrics` list from the per-rubric rates, `case_count`; invalid-point id → 404; malformed id → 422; gate declared.
- [ ] T018 [P] [US3] [api-engineer] Write tests for R4: cases merged by `eval_id` from the per-case scores and the per-case diagnostics (a case present in only one source still renders); `rubrics` with `score` and `explanation_available`; `unscored_rubrics`; `unavailable_metrics` with reason `evidence_unavailable`/`judge_unavailable`; paging bounds (`limit` 1–200 default 50); **no judge text in any field**; unknown evaluation → 404.
- [ ] T019 [P] [US3] [api-engineer] Write tests for R5: static descriptors for both metric ids with scale 0–1, `higher_is_better` true for both, label «Fidelidad a la evidencia» for `hallucinations_v1`; no database access; gate declared.
- [ ] T020 [US3] [api-engineer] Implement R3 and R4 in `api/controllers/control_quality.py` and add the routes. Paging of cases is done after the merge. Depends on T010, T011, T014, T017, T018.
- [ ] T021 [US3] [api-engineer] Implement R5 as a static table and add the route. Depends on T014, T019.

**Checkpoint**: T017–T019 green.

---

## Phase 7 — Contract verification, documentation, handoff evidence

- [ ] T022 [US4] [api-engineer] Write and run the contract test over the new router alone (`FastAPI()` + `include_router` + `app.openapi()`, stubbing as in existing route tests): asserts the five paths, parameters and bounds, `response_model` presence, and that **no response schema contains any FR-009 field name**. If this approach needs heavy stubbing, return a blocker instead of skipping it. Depends on T016, T020, T021.
- [ ] T023 [US4] [api-engineer] Add cross-cutting tests not yet covered: every new route requires the gate; unauthenticated and capability-less callers are rejected; an administrator without the capability in an existing role document is accepted. Depends on T021.
- [ ] T024 [api-engineer] Update the `soarplus-api` README (or the documentation location the repository uses for routes) with the new routes and the `quality.view` capability. Depends on T021.
- [ ] T025 [api-engineer] Run the complete `soarplus-api` unit suite and record the result. Depends on T022, T023.
- [ ] T026 [api-engineer] Write `IMPLEMENTATION-CHECKPOINT.md` in the `soarplus-api` feature directory with: what was implemented, the catalog strategy chosen (T013), the outcome of T010, the **`cassdk` impact assessment** (`YES` — additive client addition needed), test evidence, what was **not** verified (live indexes, real data, DocumentDB operator support if not exercised), and the accepted risk that the generic collection-read routes still expose `agent_eval_results`. Depends on T025.

---

## Dependencies and execution order

```text
Phase 1 (T001-T002)            withdrawn
Phase 2 (T003-T006)            independent of Phase 3
Phase 3 (T007-T011)            T010 gates T018/T020
Phase 4 (T012-T014)            needs Phase 2 + T011
Phase 5 (T015-T016)            needs Phase 4 (route module T014)
Phase 6 (T017-T021)            needs T010, T011, T014
Phase 7 (T022-T026)            needs Phases 4-6
```

Phases 2 and 3 can proceed in any order. Within `api-engineer` there is a single worker, so [P] marks
file independence, not concurrency.

## Not assigned to a worker (cannot be done by the registered workers)

| Item | Owner | Why |
|---|---|---|
| Check whether custom roles exist (`GET /rbac/roles`) | user / ops | live data (plan O-1) |
| Confirm writer indexes exist in the target environment | user / ops | no network for workers (plan R-6) |
| Smoke test on `dev` with real DocumentDB documents | user / ops | no network; closes R-3 and R-4 |
| `cassdk` client addition and version bump | unresolved — no registered worker, repository absent | return to Admiral for routing |
| Create the ADO Task and link the branch | user / Admiral | the Task does not exist yet |

## Implementation strategy

1. **MVP of the feature**: Phases 2, 3, 4, 5 (catalog + history behind the gate).
2. **Complete**: Phase 6, then Phase 7.

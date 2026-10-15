# Implementation Plan: Evolución de calidad por target — contrato de lectura en soarplus-api (fase 1)

**Feature branch**: `feature/696-sre-response-quality` | **Date**: 2026-10-15 | **Spec**: [spec.md](spec.md)

**Status**: Approved at Gate 2

> Gate: approved by user on 2026-10-15. Decisions O-1 (accept), O-2 (keep R5) and O-3 (separate paginated R4) resolved in the same session.
>
> Amendment 2026-10-15 (after Gate 2): the debug-route closure was removed from the plan (R-1 accepted, R-11 withdrawn, S1 withdrawn, §7.1 updated). Amendment accepted by the user on 2026-10-15.

**Evidence classes** used below: **[O]** observed by an analyst (path cited) · **[I]** inference by the
Captain · **[A]** assumption, unverified · **[Q]** open question.
Analyst evidence comes from `agentics-analyst` (2 reports) and `api-analyst` (2 reports) of 2026-10-15.

## Summary

`soarplus-api` publishes a read-only REST contract over `a2a_tasks.agent_eval_results` so that the
portal and `cassdk` can show how the quality of an agent, playbook or orchestrator evolves. Only
`soarplus-api` changes. The contract is exposed through an **allow-list projection**, behind a
**dedicated capability granted by default to every user**. The generic collection-read debug routes are
**not** changed by this task (spec amendment C2); that exposure stays open and is recorded as an accepted
risk.

## 1. Current system (relevant slice)

| Fact | Class | Source |
|---|---|---|
| `soarplus-agentics` is the only writer of `agent_eval_results`; one document per evaluation window and target; schema v4, mode `offline_log` is the live kind | O | `tools/sre-response-quality/sre_eval/agent_eval_result.py`, `log_eval.py` (agentics) |
| `target_type` ∈ {`agent`,`playbook`}; orchestrator = `eval_profile == "orchestrator"` | O | `sre_eval/agent_eval_result.py` |
| `target` is the agent kebab-case `real_name` or the playbook `call_name`; no owner, no playbook id in the document | O | `extract_evalset_from_mongo.py`; `soarplus-api/api/controllers/control_playbooks.py` |
| `call_name` is not globally unique; a window may mix executions of several users | O | same; `PLAN-CIERRE-Y-CONSUMO.md` §2 (agentics) |
| Only `eval_run_id` is unique. Writer declares indexes incl. `ix_target_ts (target_type,target,timestamp:-1)` and `ix_schemaver_ts (schema_version,timestamp:-1)`; creates them when an evaluation runs | O | `sre_eval/writer.py` (agentics) |
| Whether those indexes exist in the live DocumentDB, real document size and schema mix | A — not verified (no network/credentials) | — |
| `summary.metrics` never holds null: a metric without score has **no key** | O | `log_eval.py` (agentics) |
| Evaluator manifest holds 14 targets (13 enabled; 10 agents, 4 playbooks) | O | `targets.json` (agentics) |
| `soarplus-api` has no reference to `agent_eval_results`; no analogous "latest per key" query | O | `api/` (grep) |
| `GET /db/collections` and `GET /db/collections/{collection_name}` need only authentication, read any collection with `find({})`; only consumer is the admin-only DB Viewer tab | O | `api/routes/agents.py:163-186`, `api/controllers/control_agents.py:1349-1405`; frontend `src/components/ui/db-viewer-tab.tsx` |
| `require_capability` has **no** admin bypass; `authorize_capability_or_admin` has it | O | `api/utils/auth.py:86-171` |
| Existing admin role documents are not re-seeded: a new capability never reaches them automatically | O | `api/AWS/documentdb.py:1566-1592` |
| Capability grants for existing deployments use a one-shot, flagged, idempotent backfill on role `user`, run at startup in a single `try` | O | `api/AWS/documentdb.py:137-157, 1612-1670` |
| `get_effective_capabilities` reads the user's single `role`; it ignores groups | O | `api/AWS/documentdb.py:1675-1685` |
| Stack: FastAPI 0.128.0, Pydantic 2.14.1 (not pinned), pymongo 4.15.5 (sync) | O | `requirements.txt`, repo `.venv` |
| No test imports `api.api` or inspects the OpenAPI schema; tests import single route modules with `sys.modules` stubs | O | `tests/test_agents_view_all_capability.py` et al. |
| `$group`, `$sort`, `$match`, `$project` are used in the repo; `$first` and "latest per key" have no precedent; DocumentDB version/operators undocumented | O / A | `control_agents.py:1122-1249` |

## 2. Target architecture

```text
 portal / cassdk (future)
        │  GET /quality/...            (authenticated, capability quality.view)
        ▼
 routes/quality.py ──► controllers/control_quality.py ──► AWS/documentdb.py (DatabaseService)
   response_model          validation, DTO mapping            agent_eval_results_collection
   gate: capability        asyncio.to_thread                  valid-point predicate
                                                              allow-list projections
                                                              (read-only)
                                                                   │
                                                                   ▼
                                              a2a_tasks.agent_eval_results   (written by agentics only)
```

Principles that shape every decision:

1. **Allow-list, not deny-list** [I]. The writer's model is `extra="forbid"` and evolves; a deny-list
   would silently publish whatever field it adds next.
2. **One valid-point predicate**, defined once in the data-access layer and used by the catalog, the
   history and the detail, so the three can never disagree about what is a data point.
3. **API owns the contract; consumers never redefine it** (OpenAPI generated from Pydantic response
   models is the single authority).
4. **No new write path, no new index** owned by the API on `agent_eval_results`.

## 3. Contract design (design input for the API owner)

> This section is the **design-time shape**. Once implemented, the authoritative contract is the
> generated OpenAPI of `soarplus-api` (`/api/v1/openapi.json`) and the models in `api/utils/models.py`.
> From that moment this section is superseded and must not be maintained in parallel. See
> [contracts.md](contracts.md).

Prefix `/quality`, tag `Quality`. [O] no existing path uses it. JSON `snake_case`. Dates ISO-8601 UTC
strings, serialized uniformly across `evaluated_at` and `window.from/to`. Every route requires
`quality.view`.

| # | Route | Purpose |
|---|---|---|
| R1 | `GET /quality/targets` | Catalog of evaluated targets |
| R2 | `GET /quality/targets/{target_type}/{target}/evaluations` | Paginated history of one target |
| R3 | `GET /quality/evaluations/{eval_run_id}` | Detail of one evaluation, without cases |
| R4 | `GET /quality/evaluations/{eval_run_id}/cases` | Paginated evaluated cases of one evaluation |
| R5 | `GET /quality/metrics` | Static descriptors of the two metrics (no database) |

**Gate-2 decision on R5**: resolved — keep. It exists so that the label «Fidelidad a la evidencia», scale and
polarity live in one place instead of being hard-coded in the frontend and in `cassdk` (FR-006). If
rejected, FR-006 is met by OpenAPI field descriptions only.

### Shared types

```text
Metric ids (stable):  hallucinations_v1 | rubric_based_final_response_quality_v1
MetricValue   { value: float|null, n: int|null, unavailable: bool }
              value in [0,1]; null = not scored (never 0); unavailable = evaluator reported
              the metric as unavailable for this evaluation
EvaluationPoint {
  eval_run_id, evaluated_at,
  window { from, to, n, min_sample },
  status: measured | low_sample | no_activity | no_eligible_cases | evidence_incomplete,
  sample_sufficient: bool,
  evaluator { profile, profile_version, judge_model },
  metrics { hallucinations_v1: MetricValue, rubric_based_final_response_quality_v1: MetricValue }
}
```

`metrics` is a typed object with one property per metric id; both are always present. Adding a third
metric later is an additive change (FR-017).

### R1 — catalog

Query: `target_type` (enum `agent|playbook`), `eval_profile` (enum), `limit` (default 100, 1–500),
`offset` (≥0).
Item: `{ target_type, target, eval_profile, evaluations: int, latest: EvaluationPoint }`.
Envelope `{ items, total }`. Order: `target_type`, `target` ascending. `eval_profile` and `latest` come
from the most recent valid point. **No derived "kind" or `is_orchestrator` field**: orchestrators are
`eval_profile == "orchestrator"` (spec D5; avoids a second source of truth).

### R2 — history

Path: `target_type` (enum), `target` (validated against a conservative pattern, used only as a literal
equality value). Query: `limit` (default 50, 1–200), `offset` (≥0), `order` (`desc` default | `asc`).
Envelope `{ items: [EvaluationPoint], total }`. Order by `timestamp`, tie-break `eval_run_id`, so pages are
deterministic. A target with zero valid points → 404.

### R3 — detail

Path `eval_run_id` (32 lowercase hex). Response: `EvaluationPoint` + `target_type`, `target`,
`distributions { <metric id>: { n, mean, stdev, sem, min, max, p10, p50, p90 } | null }`,
`rubrics: [ { rubric_id, fulfilment_rate } ]`, `case_count`. A document that is not a valid point → 404.

### R4 — cases

Query `limit` (default 50, 1–200), `offset`. Envelope `{ items: [Case], total }`.

```text
Case {
  eval_id,                                   # task id of the evaluated execution
  metrics { <metric id>: float|null },
  rubrics: [ { rubric_id, score: 0|1, explanation_available: bool } ],
  unscored_rubrics: [ rubric_id ],
  unavailable_metrics: [ { metric_id, reason: evidence_unavailable | judge_unavailable } ]
}
```

No text produced by the judge appears anywhere in the contract (D4).

### Exposure rules (apply to every route)

Allowed source fields only: identity (`target_type`, `target`, `eval_run_id`), `eval_profile`,
`eval_profile_version`, `timestamp`/`timestamp_iso`, `summary.metrics`, `summary.unavailable_metrics`
(presence only), `raw_eval_history.window.{from,to,n,min_sample}`,
`raw_eval_history.distributions`, `raw_eval_history.by_rubric`,
`raw_eval_history.monitoring.{status,sample_sufficient,judge_model}`, `ui_detail.cases.{eval_id,metrics}`,
`raw_eval_history.case_diagnostics.{eval_id,rubric_scores,missing_rubrics,evidence_unavailable,judge_unavailable}`
and the per-rubric `rationale_available` flag only. Everything else is excluded (FR-009).

### Valid-point predicate (single definition)

A document is a series point only if **all** hold: `schema_version` 4; `mode` `offline_log`;
`raw_eval_history.monitoring.checkpoint_committed` true; `raw_eval_history.monitoring.status` is one of the
five contract statuses (so `judge_unavailable` never qualifies, spec C3); `raw_eval_history.rescore` absent
or null; `raw_eval_history.validation` absent or null. [O] basis: agentics `target_history.py` already uses
committed + `offline_log`; rescore and validation markers per `log_eval.py`/`rescore_eval.py`.
[A] whether the writer stores absent keys or explicit nulls — the engineer must handle both.

### Decisions taken by the Captain (resolving the spec's deferred list)

| Open item | Decision | Reason |
|---|---|---|
| Orchestrator in the contract | persisted `target_type` + `eval_profile` filter, no derived field | spec D5; `requestshandler` is a playbook with profile `orchestrator` [O] |
| Pagination | `offset`/`limit` + `{items,total}`, bounded with `Query(ge,le)` | same envelope as `/agents/tasks`; bounds from `usage.py` pattern [O]; paging inputs at a few hundred rows |
| Time axis | sort by `timestamp` (evaluation time); expose period separately | served by `ix_target_ts` [O]; matches user's field table |
| Metric descriptors | R5, optional | single home for labels/polarity |
| Errors | `HTTPException` string `detail`; Spanish for new messages; 404 for unknown/invalid, 422 for bad params | existing convention (mixed) [O]; no common error model exists |
| Route prefix | `/quality` | no collision found [O], not exhaustively checked |
| Index ownership | **writer (agentics) owns all `agent_eval_results` indexes; the API creates none** | `IndexOptionsConflict` risk [O]; collection low volume [A] |
| Free-text `unavailable_metrics` reasons | not exposed; only `unavailable: bool` | free text, format not a contract |
| `eval_id` in cases | exposed (user-accepted risk C1) | task read access remains enforced by the task route [O] |

## 4. Dependencies

| Class | Dependency |
|---|---|
| Design | None outward. The document semantics from `soarplus-agentics` are stable and read-only. |
| Implementation | Inside `soarplus-api`: the capability/grants are independent of the data layer; routes depend on the data layer and models. |
| Integration | Validating against real data requires a live DocumentDB in `dev` containing v4 documents. Not available to the workers. **Owner: user/ops.** |
| Merge | `soarplus-api` merges before any frontend or `cassdk` work on this contract. Nothing blocks it from agentics. |
| Deployment | API rollout runs the capability backfill automatically at startup. The writer's indexes must already exist in the target environment (verify before relying on pagination performance). |

## 5. Risks

| Id | Severity | Risk | Mitigation / owner |
|---|---|---|---|
| R-1 | HIGH | Debug routes expose the whole collection (incl. unredacted judge prose) to any authenticated user | **Accepted by the user (spec C2 withdrawn)**; not mitigated by this task; recommended separate security task |
| R-2 | HIGH | An exclusion-based projection would leak new writer fields | Allow-list projection + contract test asserting forbidden field names are absent |
| R-3 | MEDIUM | Valid-point predicate wrong on real data (absent vs null markers; legacy schemas) | Unit tests for both shapes; manual check on dev data (user/ops) |
| R-4 | MEDIUM | `$sort`+`$group`+`$first` unsupported or slow on DocumentDB | Engineer verifies on dev; documented fallback: `distinct` per type + one indexed query per target (≈14 targets today) |
| R-5 | MEDIUM | Projecting only `rationale_available` out of the nested judge structure may not be expressible | Engineer verifies the exact nested path against the writer model and fixtures. If not feasible, **return a blocker to the Captain**; do not widen the projection |
| R-6 | MEDIUM | Writer indexes may not exist live → slow catalog/history | Index check in dev by user/ops; API creates none |
| R-7 | MEDIUM | Users with a **custom** role do not receive the default grant (the backfill targets the predefined `user` role) | Accepted (O-1); admin grants it by hand |
| R-8 | MEDIUM | Blocking pymongo calls in `async def` | `asyncio.to_thread` (precedent `control_agents.py:1012`); the MTA controller is **not** a model |
| R-9 | MEDIUM | The RBAC startup calls share one `try`; an earlier failure silently skips the new backfill | Call the new backfill last; test that it runs |
| R-10 | LOW | Offset paging can shift while new evaluations are written | Documented; evaluations arrive at most per scheduled run |
| R-11 | — | *(Withdrawn: debug routes are not changed.)* | — |
| R-12 | INFO | Private playbook names may appear in the catalog | Accepted by user (spec C1); curated targets only today |
| R-13 | INFO | `cassdk` is not present; its impact is inference only | Recorded; returned to Admiral as unresolved requirement |

## 6. Decisions resolved at Gate 2

- **O-1 — RESOLVED: accept.** Users on custom roles do not get `quality.view` by default; only the
  predefined `user` role is granted (new and existing deployments). An administrator grants it to custom
  roles by hand. Before relying on "open to everyone", an administrator should check whether custom roles
  exist (`GET /rbac/roles`); that check is a user/ops step.
- **O-2 — RESOLVED: keep** R5 (`GET /quality/metrics`).
- **O-3 — RESOLVED: separate paginated route** R4; cases are not embedded in R3.

## 7. Per-repository plans

### 7.1 soarplus-api (owner of the contract)

**Objective.** Implement R1–R5 (R5 per O-2), the capability and its default grant. The generic
collection-read debug routes are out of scope.

**Approach** (layers, following the repository's own conventions).
- *Data access* — `api/AWS/documentdb.py`: add an `agent_eval_results_collection` attribute on
  `a2a_tasks` and read-only query methods that embed the valid-point predicate and the allow-list
  projections. The API creates **no** index on this collection.
- *Controller* — `api/controllers/control_quality.py`: validation, DTO mapping, 404 handling.
  Synchronous pymongo calls via `asyncio.to_thread`. Never pass user input as a query document:
  `target`, `target_type`, `eval_profile`, `order` and `eval_run_id` are validated (enum or strict
  pattern) and used as equality literals.
- *Models* — `api/utils/models.py`: Pydantic response models for every type in §3, with
  `response_model` on every route so that OpenAPI describes the contract.
- *Routes* — `api/routes/quality.py`: router prefix `/quality`, tag `Quality`; register in `api/api.py`
  (import, `include_router`, `tags_metadata`). Every route declares the gate as a dependency.
- *RBAC* — add capability `quality.view` to `api/rbac_capabilities.py`. Gate with
  `authorize_capability_or_admin(controller, "quality.view")` (admin bypass already present, so existing
  admin role documents do not lock admins out). Do **not** use `require_capability` here.
  Grant by default: add the id to the predefined `user` baseline for new deployments and add a one-shot,
  flagged, idempotent `ensure_..._backfilled` for existing deployments, invoked **last** in the startup
  block, following the pattern of `ensure_llm_config_override_agent_pin_capability_backfilled`.
- *Catalog query* — preferred: aggregation (valid points → latest per `(target_type,target)` + count).
  If DocumentDB does not support it, use the fallback of R-4. State which one was used in the checkpoint.

**Constraints.**
- Repository constitution and `AGENTS.md`/`.github/copilot-instructions.md` prevail (TDD, no inline
  models, layering, no blocking I/O in async code).
- The API MUST NOT write to `agent_eval_results`, MUST NOT create indexes on it, and MUST NOT expose any
  field outside the allow-list of §3.
- Do not reuse the `GET /agents/tasks` or MTA code as a template for bounds: they leave `limit` unbounded
  or block the event loop. Use `Query(ge, le)`.

**Contracts provided.** R1–R5 (REST), capability `quality.view` (permission). See [contracts.md](contracts.md).

**Contracts consumed.** The persisted document shape of `agent_eval_results` v4 (data contract, owned by
`soarplus-agentics`). Existing task read route for per-case follow-up (unchanged).

**Out of scope, do not touch.** `GET /db/collections` and `GET /db/collections/{collection_name}` keep
their current behaviour. The engineer records in the checkpoint that `agent_eval_results` remains readable
through them by any authenticated user.

**Validation expectations.**
- `unittest`, no network, `AWS.*` mocked per `testing.instructions.md`; written before the code.
- Tests: capability registered and in the `user` seed; backfill idempotent and runs last; each new route
  uses the gate; valid-point predicate (rescore, validation,
  uncommitted, `judge_unavailable`, wrong schema/mode, absent-vs-null markers); allow-list projection
  contains none of the FR-009 fields; paging bounds (`limit`, `offset`, `order`); operator-injection
  strings treated as literals or rejected (422); 404 cases; deterministic order with equal timestamps.
- Contract test over the new router alone (`FastAPI()` + `include_router` + `app.openapi()`), asserting
  paths, parameters and that no response schema contains a FR-009 field name. [A] this approach has not
  been run in this repository; if it needs heavy stubbing, return a blocker rather than skip it.
- Existing suites touching the capability catalog (`test_rbac_capabilities.py`,
  `test_predefined_roles_seeding.py`) must still pass.
- `cassdk` impact assessment (`YES` additive / `NO`) recorded in `IMPLEMENTATION-CHECKPOINT.md`.
- Manual smoke on `dev` with real DocumentDB: **not performable by workers**; reported as a user/ops step.

### 7.2 soarplus-agentics — not affected

No change. Provider of the data contract. Its documents must not be modified or re-indexed from this
feature. If the `rationale_available` projection (R-5) proves impossible, the fallback conversation is
with the Captain, not an assumption that agentics will change the document.

### 7.3 soarplus-frontend-app1 — not affected in this phase

Future consumer; must generate/consume types from the published contract and must not define shapes. The
admin DB Viewer tab is unaffected by this task. [O]

### 7.4 cassdk — unresolved orchestration requirement

Not present in this environment and has no registered worker. The new routes are additive, so no existing
`cassdk` contract changes [I]. A client addition and a version bump are needed when `cassdk` exposes this
view. **Not assigned to any worker**; returned to the Admiral for routing.

### 7.5 soarplus-kubernetes — not established

No new environment variable or configuration is introduced. Only the verification of the writer's indexes
and of the evaluator's effective minimum sample (`EVAL_MIN_SAMPLE`) touches that repository, and neither
is a change.

## 8. Sequencing

```text
S1  (withdrawn)                              debug-route closure removed from scope
S2  capability + default grant + backfill    independent of S3
S3  data-access layer: predicate + projections + models
S4  R1 catalog, R2 history                   needs S2, S3
S5  R3 detail, R4 cases, R5 metrics          needs S3; may follow S4
S6  contract test, docs, cassdk assessment, checkpoint
```

Execution is by `api-engineer` only; no cross-repository ordering constraint within this phase.

## 9. Validation strategy (global)

| Level | Who | Evidence |
|---|---|---|
| Unit and contract tests | `api-engineer` | test run in the Task Result |
| Security acceptance (SC-002) | `api-engineer` | tests for allow-list and gate |
| Real-data smoke on `dev` | user / ops | manual; recorded by the Admiral as unverified until done |
| Index existence and live collection size | user / ops | manual |

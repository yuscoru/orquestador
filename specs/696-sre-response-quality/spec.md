# Feature Specification: Evolución de calidad por target — contrato de lectura en soarplus-api (fase 1)

**Feature Branch**: `feature/696-sre-response-quality`

**Created**: 2026-10-15

**Status**: Approved at Gate 1

> Gate: approved by user on 2026-10-15. Clarifications C1, C2, C3, D4 and D5 resolved by the user in the same session.
>
> Amendment 2026-10-15 (user, after Gate 1): C2 withdrawn; FR-011, SC-004 and US4 scenario 3 withdrawn. The
> generic collection-read routes stay out of scope. Ids are kept so existing references remain valid.
>
> Amendment accepted: the user explicitly accepted this amendment of the approved spec on 2026-10-15.

**Parent User Story**: Azure DevOps #696 (SRE de Calidad de IA — Capa 1 / Response Quality)

**ADO Task**: #801, child of #696 (created 2026-10-15).

**Input**: "Construir una vista de evolución de calidad por target (agente, playbook, orquestador). En esta fase se planifica únicamente el contrato en soarplus-api, que lo publica para el front y para cassdk."

## Scope of this global spec

This directory is keyed by the User Story (`696-sre-response-quality`). The producer side of #696
(evaluator, persistence in `a2a_tasks.agent_eval_results`) is already specified and implemented in
`soarplus-agentics/specs/696-sre-response-quality/` and is **not** re-specified here.

This spec covers one increment: **making the persisted evaluations readable by consumers through a
stable, safe REST contract published by `soarplus-api`.**

| In scope (phase 1) | Out of scope (later) |
|---|---|
| Contract and API implementation in `soarplus-api`: target catalog, paginated history per target, detail of one evaluation | Portal view (`soarplus-frontend-app1`) |
| Access control and data-exposure rules for that contract | `cassdk` client update (repo not present in this environment; impact assessment still required) |
| Impact assessment on `cassdk` and the frontend | Automatic comparison between periods, alerts, explanation of differences between periods |
| | Changes to the evaluator or to the persisted document (`soarplus-agentics`) |

> Scope note: `soarplus-agentics/specs/696-sre-response-quality/PLAN-CIERRE-Y-CONSUMO.md` §5 describes
> consumption as a feature separate from #696, while `cross-repo-branches.md` lists a trend endpoint
> inside #696. The user has decided this work is a task **within** #696. Recorded here so the
> inconsistency is visible; the agentics documents are not corrected from this repository.

## User Scenarios & Testing *(mandatory)*

The "users" of this contract are its consumers: the portal (via `soarplus-frontend-app1`) and SDK
users (via `cassdk`). The end user behind them is an SRE or platform owner who wants to know whether
the quality of an agent, playbook or orchestrator is improving or degrading over time.

### User Story 1 - Discover which targets have quality measurements (Priority: P1)

A consumer asks which targets have been evaluated and gets one entry per target with enough context
to choose one: type, name, evaluation profile, whether it is an orchestrator, when it was last
evaluated and the status of that last measurement.

**Why this priority**: Without a catalog no consumer can offer a target selector; the history is
unreachable.

**Independent Test**: Call the catalog with an authorized identity against a collection seeded with
evaluations of several agents and playbooks; each target appears once, with its latest-measurement
summary, and targets that are not valid series points do not distort it.

**Acceptance Scenarios**:

1. **Given** evaluations exist for agents and playbooks, **When** the catalog is requested, **Then**
   every target with at least one valid evaluation appears exactly once with its type, name,
   evaluation profile and last-measurement timestamp and status.
2. **Given** a target whose only documents are rescores, validation runs or runs whose judge was
   unavailable, **When** the catalog is requested, **Then** that target does not appear as having a
   measured history.
3. **Given** the consumer filters by target type or by orchestrator profile, **When** the catalog is
   requested, **Then** only matching targets are returned.

---

### User Story 2 - See how the two quality metrics evolve for a target (Priority: P1)

A consumer asks for the history of one target and receives a time-ordered, paginated series. Each
point carries the two headline metrics, the sample size behind them, the measurement status, the
evaluated period and the evaluator context (profile, profile version, judge model), so a change in
how quality is measured is visible next to a change in quality.

**Why this priority**: This is the core of the feature — the evolution view.

**Independent Test**: Request the history of a seeded target; points arrive ordered by evaluation
time, paginated, each with both metrics (or an explicit absence), `n`, status, period and evaluator
context; no point comes from a rescore, a validation run or an uncommitted window.

**Acceptance Scenarios**:

1. **Given** a target with many valid evaluations, **When** the history is requested with a page
   size, **Then** a bounded page is returned in a defined order together with what is needed to fetch
   the next page.
2. **Given** a point where a metric has no score, **When** it is returned, **Then** the metric is
   explicitly absent (not `0`), and the status says why the point has no metrics.
3. **Given** two consecutive points with different evaluator profile version or judge model,
   **When** they are returned, **Then** the difference is observable from the point data alone.
4. **Given** a point whose status is low sample, no activity, no eligible cases or incomplete
   evidence, **When** it is returned, **Then** the consumer can distinguish it from a normal
   measurement without interpreting free text.
5. **Given** a target name that does not exist, **When** the history is requested, **Then** the
   consumer receives a defined "not found" or empty result according to the contract.

---

### User Story 3 - Inspect one evaluation in depth (Priority: P2)

A consumer opens a single evaluation and sees: the evaluated period and the executions it speaks
about; per metric the sample size, median, percentiles and dispersion; the fulfilment rate per
rubric; the measurement state; the evaluated cases with their scores; and per case the rubric
outcomes and which explanations exist — without the explanations' text.

**Why this priority**: Explains *why* a point moved, but the evolution view is useful without it.

**Independent Test**: Request the detail of a seeded evaluation; all listed groups are present and a
payload scan finds none of the excluded fields (see FR-009).

**Acceptance Scenarios**:

1. **Given** a valid evaluation id, **When** the detail is requested, **Then** distributions per
   metric, rubric fulfilment, measurement state, period, evaluator context and evaluated cases are
   returned.
2. **Given** an evaluation with up to several hundred cases, **When** the detail is requested,
   **Then** the response is bounded in size (cases paginated or capped by contract).
3. **Given** a case with rubric outcomes, **When** it is returned, **Then** it exposes each rubric's
   outcome, the rubrics that could not be scored, and a flag per rubric stating whether an
   explanation exists, but no explanation text.
4. **Given** an evaluation id that is not a valid series point, **When** requested, **Then** it is
   treated as not found.

---

### User Story 4 - Only authorized consumers read quality data, and only safe fields leave the API (Priority: P1)

Quality evaluations are internal operational data. The contract applies authorization and publishes
only an explicit allow-list of fields.

**Why this priority**: The source documents contain judge prose with excerpts of responses and tool
output, not anonymized for PII. A contract that is correct but leaks them is a defect.

**Independent Test**: Call every new route with an unauthenticated identity, an authenticated
identity without permission, and an authorized one; and attempt to read the same collection through
every other API route.

**Acceptance Scenarios**:

1. **Given** an unauthenticated or unauthorized identity, **When** any new route is called, **Then**
   access is denied.
2. **Given** an authorized identity, **When** any new route is called, **Then** no response contains
   any field listed in FR-009.
3. *(Withdrawn 2026-10-15, see C2.)* The generic collection-read debug routes are **not** changed by
   this task; they remain a known exposure outside this contract.

---

### Edge Cases

- A target has documents of several schema versions or modes (legacy designs coexist in the
  collection): only the current valid kind appears.
- Overlapping windows: rescores repeat the cases of a source run; windows of uncommitted runs overlap
  the next one. They must not create duplicate or overlapping points.
- A metric key is absent in a document (no score): returned as explicit absence, never `0`.
- A `hallucinations_v1` value of `0` can be structural (no tool evidence in the trace), not proof of
  hallucination; the contract must let consumers surface that caveat (see FR-006).
- `target` is a free string and is not unique across types or across owners: the contract must key
  targets by `(target_type, target)` and never by name alone.
- The same playbook name may belong to different users, and a window may mix executions of several
  users; the persisted document carries neither owner nor playbook id.
- A target that was renamed or deleted keeps its documents and keeps appearing in the catalog.
- Targets never evaluated are absent from the catalog; the catalog is *evaluated targets*, not a
  directory of all agents and playbooks.
- Documents can reach a few hundred cases; projections must bound payload.
- Filter inputs containing query operators must be treated as literals or rejected.
- Orchestrators: there is no persisted `target_type` for them; they are identified by evaluation
  profile. `callagent-orchestrator` is `agent` + `orchestrator`; `requestshandler` is `playbook` +
  `orchestrator`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `soarplus-api` MUST publish a read-only contract with three capabilities: a catalog of
  evaluated targets, a paginated history per target, and the detail of one evaluation. It MUST NOT
  write to `agent_eval_results`.
- **FR-002**: A target MUST be identified in the contract by the pair `(target_type, target)`, using
  the values persisted by the evaluator. `target_type` MUST be limited to the persisted values
  (`agent`, `playbook`). The API MUST NOT invent a third `target_type`.
- **FR-003**: The contract MUST let a consumer select agents, playbooks and orchestrators.
  Orchestrators MUST be selectable through the persisted evaluation profile. *(How the three groups
  are expressed in the contract is a Gate-2 design decision.)*
- **FR-004**: The history and the catalog MUST include only valid series points: schema version 4,
  offline-log mode, committed measurement window, and not a rescore nor a historical-persistence
  validation. Anything else MUST be excluded or rejected consistently.
- **FR-005**: Each history point MUST expose: evaluation timestamp; evaluated period (from/to);
  the two metrics `hallucinations_v1` and `rubric_based_final_response_quality_v1` on a 0–1 scale,
  with explicit absence when not scored; the sample size per metric and for the window; measurement
  status; evaluation profile, profile version and judge model.
- **FR-006**: The contract MUST convey, for each metric, its scale and polarity so consumers cannot
  misread a high `hallucinations_v1` as bad. `hallucinations_v1` MUST be presented to users as
  «Fidelidad a la evidencia». The contract MUST also carry enough information for a consumer to tell
  that a low value may reflect missing evidence rather than hallucination (reason available when the
  evaluator reported the metric as unavailable or evidence as incomplete).
- **FR-007**: Measurement status MUST be machine-readable and limited to the evaluator's states:
  measured, low sample, no activity, no eligible cases, evidence incomplete. It MUST NOT require
  parsing free text.
- **FR-008**: The detail of an evaluation MUST expose: period; per-metric distribution (count, mean,
  standard deviation, standard error, min, max, p10, p50, p90); per-rubric fulfilment rate;
  measurement state; evaluated cases with their per-metric scores; per-case rubric outcomes,
  unscored rubrics and an indicator per rubric of whether an explanation exists.
- **FR-009**: No response of this contract MUST contain: judge-generated text (sentences, rationales,
  supporting or contradicting excerpts), the internal construction trace, published-deliverable
  provenance, tracking/telemetry, root task ids lists, execution trees, evaluator fingerprint or
  source reference, or vestigial fields (`passed`, `thresholds`, `invocations`, baseline
  comparability). Field exposure MUST be an allow-list, not a deny-list.
- **FR-010**: Access MUST require authentication and an explicit authorization decision for these
  routes, through a dedicated capability that administrators always hold implicitly. The capability
  MUST be granted by default to every authenticated user (base role) on new and existing
  deployments, so that today any authenticated user can read. Administrators MUST NOT be locked out
  by a missing grant. Restricting access later (for example to a specific role) MUST be a permission
  change only, with no change to the contract or the routes. *(Resolution: C1.)*
- **FR-011**: *(Withdrawn 2026-10-15, see C2.)* This task does not change the generic collection-read
  debug routes. The allow-list guarantee of FR-009 applies to the routes of this contract only.
- **FR-012**: Lists MUST be bounded: page size has a documented default and hard maximum; invalid
  paging inputs are rejected; the history order is deterministic and stable across pages.
- **FR-013**: User-supplied filters (target name, type, profile, dates) MUST be validated against
  allow-lists or treated as literals; operator injection MUST NOT alter the query.
- **FR-014**: Data access MUST use bounded projections and MUST NOT block the API event loop.
- **FR-015**: The contract MUST be stable and documented as its single authoritative description
  (published OpenAPI schema of `soarplus-api`) so that `soarplus-frontend-app1` and `cassdk` consume
  it without redefining shapes. Field naming and date formats MUST follow the existing API
  conventions.
- **FR-016**: The change MUST include an explicit `cassdk` impact assessment recorded in the
  `soarplus-api` implementation checkpoint.
- **FR-017**: The contract MUST NOT carry automatic period comparison, alerts or explanations of
  differences between periods in this phase. It MUST be extensible to add them without breaking
  existing fields.

### Clarifications and decisions

- **C1 — RESOLVED (user, 2026-10-15): open to every authenticated user, prepared for a role and a
  capability.**
  - One new dedicated capability for reading quality data (catalog, history, detail), with admin
    bypass, granted by default to the base user role. Restricting later is a permission change.
  - **Accepted risk (owner: user)**: the catalog lists `target` names; for playbooks that is a
    `call_name` that is not globally unique and has no owner (observed), so the name of a private
    playbook that is evaluated could be visible to users who cannot see the playbook. The per-case
    `eval_id` also exposes task ids of other users' executions (task read access itself stays enforced
    by the existing task route). Today only curated targets are evaluated (analyst evidence: 14 entries
    in the evaluator manifest, 4 playbooks), which bounds the exposure.
  - **No per-target scoping**: a faithful scoping needs owner/playbook id, which the document does
    not carry, and one evaluation window may mix executions from several users.
  - Follow-up noted, not part of this task: review the general API behaviour regarding routes gated
    only by authentication.
- **C2 — WITHDRAWN by the user on 2026-10-15 (amends the Gate 1 decision): the generic collection-read
  routes are NOT closed in this task.**
  - Reason given by the user: the routes affect the whole API, and closing them abruptly is not
    wanted now.
  - **Accepted risk (owner: user)**: `GET /db/collections` and `GET /db/collections/{collection_name}`
    (tag "DB Debug", `api/routes/agents.py`, `api/controllers/control_agents.py`) read any collection of
    the database or of `a2a_tasks.*` with `find({})` and no projection, gated only by authentication.
    Any authenticated user can therefore read the whole of `agent_eval_results`, **including the judge
    prose** (excerpts of responses and tool output, not anonymized for PII) that this contract
    deliberately does not expose. The allow-list contract does not protect that data while the routes
    stay open.
  - Observed context kept for whoever later decides: the matching DELETE already requires admin
    (`api/routes/info.py`); the only known consumer of the GETs is the admin-only DB Viewer tab of
    `soarplus-frontend-app1`; callers outside the three repositories were not verified.
  - Recommended follow-up, **separate from this task**: a dedicated security task for those routes, with
    its own impact analysis on the whole API.
- **C3 — RESOLVED**: runs whose judge was unavailable produce no result and no point in the series.
  They are excluded from catalog, history and detail.
- **D4 — RESOLVED**: no judge text in this phase. The detail exposes rubric outcomes and an
  "explanation exists" indicator per rubric only.
- **D5 — RESOLVED**: no third `target_type`. Orchestrators are selected by the persisted evaluation
  profile; how that is expressed in the contract remains a Gate-2 decision.

### Key Entities

- **Evaluated target**: an agent or playbook with at least one valid evaluation, identified by
  `(target_type, target)`; carries its evaluation profile and latest-measurement summary. An
  orchestrator is an evaluated target whose profile is `orchestrator`.
- **Evaluation (series point)**: one measurement of a target over a window of historical executions.
  Has a unique run id, an evaluation timestamp, a period, headline metrics, sample sizes, a status and
  evaluator context.
- **Metric**: `hallucinations_v1` (evidence fidelity, higher is better) and
  `rubric_based_final_response_quality_v1` (quality by applicable rubrics), both 0–1.
- **Distribution**: statistics of one metric over the evaluated cases of one evaluation.
- **Rubric result**: fulfilment rate of one rubric across an evaluation; per-case outcome in the detail.
- **Evaluated case**: one historical execution scored in an evaluation, referenced by its task id.
- **Evaluator context**: evaluation profile, profile version and judge model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every evaluated target, a consumer can retrieve its complete valid history by
  following pages, with no point repeated, omitted or out of order.
- **SC-002**: In 100% of automated checks over responses of all new routes, none of the fields in
  FR-009 appears.
- **SC-003**: 100% of the new routes deny unauthenticated and unauthorized callers; an administrator
  can use them on an existing deployment without a manual role migration.
- **SC-004**: *(Withdrawn 2026-10-15, see C2.)*
- **SC-005**: A consumer can render both series, sample size and status per point using only this
  contract, without reading the database or any legacy field.
- **SC-006**: Invalid paging, filters and operator-injection attempts yield rejection or literal
  handling in 100% of tested cases.
- **SC-007** *(proposed, to be validated against real data before it becomes a gate)*: a history page
  for a target with a few hundred evaluations is returned in a time compatible with interactive use.

## Assumptions

Marked by evidence class. Source: analyst reports of 2026-10-15 (`agentics-analyst`, `api-analyst`);
they are not persisted separately, so the facts that matter are restated here by reference.

**Observed (analyst evidence)**

- `soarplus-agentics` is the only writer of `a2a_tasks.agent_eval_results` and needs no change for
  this task. Model: `tools/sre-response-quality/sre_eval/agent_eval_result.py`; builder:
  `tools/sre-response-quality/log_eval.py`.
- Persisted `target_type` values are only `agent` and `playbook`; orchestrator is the evaluation
  profile `orchestrator` (`sre_eval/agent_eval_result.py`).
- Only `eval_run_id` is unique. Index `ix_target_ts` (target_type, target, timestamp desc) is declared
  by the writer (`sre_eval/writer.py`).
- `summary.metrics` never contains null; a metric without score has no key. Metric scale 0–1.
- `raw_eval_history.monitoring.status` values: `measured`, `low_sample`, `no_activity`,
  `no_eligible_cases`, `evidence_incomplete`, `judge_unavailable`.
- Judge prose (`raw_eval_history.case_diagnostics[].judge_diagnostics`) is not anonymized for PII
  (`specs/696-sre-response-quality/IMPLEMENTATION-CHECKPOINT.md` in agentics, around line 3105).
- No code in `soarplus-api` references `agent_eval_results`; the generic route
  `GET /db/collections/{collection_name}` is gated only by authentication and can dump it
  (`api/routes/agents.py`, `api/controllers/control_agents.py`).
- `soarplus-api` has no versioned OpenAPI file and no contract tests (`api/api.py` serves OpenAPI).
- Existing patterns to follow: `api/routes/mta.py` + `api/controllers/control_mta.py` (list + detail
  with explicit projection) and `api/routes/usage.py` (validated `Query` bounds).

**Inference (Captain)**

- A global-capability model (C1) is the only one implementable without new data the evaluator does not
  persist.
- Allow-list projection is required because exclusion-based projection would silently expose any
  field the writer adds later.

**Not verified (carried as risks into the plan)**

- Real documents in DocumentDB: nothing was read (no network or credentials); sizes, schema mix and
  indexes in the live database are unknown.
- Whether the evaluation CronJob is deployed and what `EVAL_MIN_SAMPLE` it uses; the effective
  low-sample threshold may be 1.
- `cassdk` structure and publishing process (repository absent).

**Open decisions deferred to the plan (Gate 2)**: orchestrator representation in the contract,
pagination style, time axis for the series, metric descriptor ownership, error format, route prefix,
index ownership, treatment of free-text `unavailable_metrics` reasons.

**Unresolved orchestration requirements**

- `cassdk` has no registered worker and is not present in this environment. Whatever it needs is
  returned to the Admiral, not assigned.
- `soarplus-kubernetes` may be affected only if index creation or a role/capability migration needs
  deployment configuration; not established.

## Affected repositories

| Repository | Affected | Role |
|---|---|---|
| `soarplus-api` | **yes** | Provider of the contract (owner) |
| `soarplus-agentics` | no | Provider of the data; unchanged. Source of the document semantics |
| `soarplus-frontend-app1` | no (this phase) | Future consumer; must not define shapes |
| `cassdk` | not verifiable | Future downstream consumer; impact assessment required |

# Contract registry — 696-sre-response-quality

References only. A contract has exactly one authoritative source; nothing here duplicates a shape.

**Status**: Approved with plan.md at Gate 2 on 2026-10-15 (see [plan.md](plan.md) §3 for the design-time shape).

## C-01 quality-read-api

*(amended by CR-001, DRAFT: surface R1–R6; R2 becomes `GET /quality/targets/{target}/evaluations`
with last-5 scored points and 409 collision guard; new R6 `GET /quality/targets/history`;
scored-point predicate replaces the valid-point predicate — see plan.md §3 and changes/CR-001.md)*

*(amended by CR-002: `EvaluationPoint.status` and `sample_sufficient` are nullable — null for legacy
documents without the monitoring block; see changes/CR-002.md)*

*(amended by CR-004; revised delta approved 2026-10-22: change `EvaluationPoint.status` from a closed enum to
nullable open string. R1/R2/R3/R6 preserve known/future writer strings; null remains legacy-only;
malformed non-string metadata becomes API sentinel `invalid_status` with safe type-only logging.
Consumers need known branches plus a generic degraded default.)*

```yaml
name: quality-read-api
type: REST
provider: soarplus-api
consumers:
  - soarplus-frontend-app1   # future phase
  - cassdk                   # future phase; not present in this environment
authoritative_source: >
  Before implementation: plan.md §3 (design input). After implementation: generated OpenAPI of
  soarplus-api (/api/v1/openapi.json) from the response models in api/utils/models.py in
  soarplus-api. From that moment plan.md §3 is superseded.
compatibility: >
  Amended by CR-001 before any consumer exists: R2 URL and semantics change (breaking versus the
  unreleased previous shape), R6 added. CR-004 proposes changing status from enum-or-null to
  string-or-null; existing JSON values remain compatible but exhaustive/generated consumers must
  add a default branch. No existing route outside this feature changes shape. Metric ids are stable;
  new metrics are added as new properties.
```

## C-02 quality-view-capability

```yaml
name: quality.view
type: capability / permission
provider: soarplus-api
consumers: [soarplus-frontend-app1, cassdk]
authoritative_source: api/rbac_capabilities.py in soarplus-api
compatibility: >
  Granted by default to the predefined user role (new and existing deployments); admin bypass.
  Restricting access later is a permission change, not a contract change. Users on custom roles do
  not receive it by default (accepted, plan.md O-1).
```

## C-03 agent-eval-result-document

```yaml
name: agent_eval_results document v4 (schema_version 4, mode offline_log)
type: persistence schema
provider: soarplus-agentics
consumers: [soarplus-api]
authoritative_source: tools/sre-response-quality/sre_eval/agent_eval_result.py in soarplus-agentics
compatibility: >
  Read-only for this feature. Several legacy document kinds coexist in the collection; the API reads
  only the valid-point kind defined in plan.md §3. The writer's model forbids extra fields, so
  allow-list projection is mandatory. The writer-supported monitoring status `judge_unavailable`
  is observed and covered by CR-004; the writer schema itself is unchanged.
```

## C-04 debug-collection-read-routes (withdrawn)

Not changed by this feature (spec amendment C2, 2026-10-15). Kept as a registry entry so the decision is
visible.

```yaml
name: GET /db/collections, GET /db/collections/{collection_name}
type: REST
provider: soarplus-api
consumers: [soarplus-frontend-app1 admin DB Viewer tab]
authoritative_source: api/routes/agents.py in soarplus-api
compatibility: >
  No change in this feature. Currently gated by authentication only. Known consumer is the admin-only
  DB Viewer. Callers outside the three repositories were not verified.
```

## C-05 evaluator-minimum-sample (deployment configuration, not owned here)

```yaml
name: EVAL_MIN_SAMPLE / targets min_sample
type: deployment/configuration contract
provider: soarplus-agentics (code), soarplus-kubernetes (CronJob env)
consumers: [soarplus-api]   # only as context for the low_sample status
authoritative_source: agents/system-agent/tools_sre_quality.py in soarplus-agentics
compatibility: not verified; effective threshold may be 1
```

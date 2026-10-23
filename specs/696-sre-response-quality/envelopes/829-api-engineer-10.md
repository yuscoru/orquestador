# Operational Envelope — API — implement CR-004 forward-compatible Quality status (E10)

Issued after user approval of revised CR-004 and verified creation of ADO Task #829.

```yaml
mode: IMPLEMENT
kind: CHANGE
cr: CR-004
feature: 696-sre-response-quality
assignment: {id: 696-api-11, ado_task: 829, spec_tasks: [T041]}
repository: {name: soarplus-api, path: /root/soarplus-api, branch: feature/696-sre-response-quality, expected_head: f34bf9c48ab05a845e37dac5263048c64cec1a3d}
objective: >
  Implement T041: change QualityEvaluationPoint.status to an open nullable string (no OpenAPI enum),
  preserve all current and future writer strings, keep null exclusively for legacy missing monitoring,
  and map malformed non-string metadata to the fixed sentinel `invalid_status` with type-only structured logging.
acceptance_criteria:
  - TDD rule: tests written first under `tests/` demonstrating the open-string contract, known writer strings
    (measured, low_sample, no_activity, no_eligible_cases, evidence_incomplete, judge_unavailable), arbitrary future string
    preservation (e.g. `future_status_x`), legacy null, and the malformed non-string boundary mapping to `invalid_status`.
  - In `api/utils/models.py`, `QualityEvaluationPoint.status` is typed `Optional[str] = Field(default=None, ...)`.
    No OpenAPI enum is emitted for status.
  - In `api/controllers/control_quality.py` (`map_evaluation_point`), preserve non-null string status values literally.
    If the persisted status is non-null and not a string, set status to `invalid_status` and log a structured warning/error
    containing eval_run_id, target, and the value's type name, but never the raw malformed value.
  - Routes R1, R2, R3, R6 serialize without 500 when status is `judge_unavailable`, an arbitrary future string, or `invalid_status`.
  - Routes R4 (cases) and R5 (metrics) remain unchanged and green.
  - Run the targeted test suite and the complete unit test suite; verify no regressions.
  - Clean git commit on feature/696-sre-response-quality with trailer `Refs: #696 #829`.
  - Update local `specs/696-sre-response-quality/IMPLEMENTATION-CHECKPOINT.md`.
  - Do not push to remote; do not open a PR.
delivery: {update_ado: true, commit: true, push: false, create_pr: false, deploy: false}
```

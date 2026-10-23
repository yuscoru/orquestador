# Operational Envelope — Frontend — implement CR-004 degraded Quality status rendering (F8)

Issued after API completion of T041 under CR-004 and verified creation of ADO Task #830.

```yaml
mode: IMPLEMENT
kind: CHANGE
cr: CR-004
feature: 696-sre-response-quality
assignment: {id: 696-frontend-14, ado_task: 830, spec_tasks: [T042, T043]}
repository: {name: soarplus-frontend-app1, path: /root/soarplus-frontend-app1, branch: feature/696-sre-response-quality, expected_head: 0032c688ff7db894e96c3d0a441c75334a40241f}
objective: >
  Implement T042 and validate T043: update frontend Quality types to open string|null, centralize
  known/default status classification, render judge_unavailable, invalid_status and future unknown
  strings as degraded (never default/green or zero), and validate via build, lint, and browser evidence.
acceptance_criteria:
  - In `src/lib/types.ts`, change `QualityMeasurementStatus` or `QualityEvaluationPoint.status` typing to
    `string | null` (retaining documented known literals for autocomplete/typing while accepting any string).
  - In `src/components/ui/quality-shared.tsx`, update `statusLabel` and status classification helpers:
    - `measured`: normal/measured.
    - `null` / `undefined`: "unknown (legacy)".
    - `judge_unavailable`: "judge unavailable" (known degraded).
    - `invalid_status`: "invalid status" (malformed persisted status).
    - any other string: preserve the string or format cleanly as degraded (never green/default).
  - In `src/components/ui/quality-catalog-table.tsx` and `quality-points-table.tsx`:
    - Only `status === "measured"` uses `variant="default"`.
    - `judge_unavailable`, `invalid_status`, and unknown strings use a degraded/secondary/warning badge.
    - Legacy null points keep their distinct outline/"unknown (legacy)" presentation.
  - In `src/components/ui/quality-evolution-chart.tsx`:
    - Ensure chart dots for degraded points (judge_unavailable, invalid_status, unknown) are visually
      distinguished from normal measured points (e.g. distinct stroke/marker or warning pattern) and
      do not plot as 0 when metric values are present. For null metric values, maintain gaps.
    - Add a concise note or legend indication for degraded measurement points.
  - Verification (T043):
    - `npm run lint` passes at or better than baseline.
    - `npm run build` succeeds cleanly.
    - Verify with existing evidence/harness or local browser checks that known degraded, future unknown,
      invalid sentinel, metric-null, and legacy status-null points render as expected.
  - Clean git commit on feature/696-sre-response-quality with trailer `Refs: #696 #830`.
  - Update local `specs/696-sre-response-quality/IMPLEMENTATION-CHECKPOINT.md`.
  - Do not push to remote; do not open a PR.
delivery: {update_ado: true, commit: true, push: false, create_pr: false, deploy: false}
```

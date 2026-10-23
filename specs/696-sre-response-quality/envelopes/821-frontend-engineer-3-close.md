# Task Envelope — 821 — frontend-engineer — CR-003 closure (F3)

Issued 2026-10-20 by the admiral. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: CHANGE_CLOSURE
change_request: CR-003
feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality
  prior_result: results/2026-10-20-frontend-engineer-821-2-partial.md
  user_validation: >
    User confirmed on 2026-10-20, using the automatically refreshed npm run dev UI, that the
    complete requested drawer result works and looks correct. This closes the manual browser
    checklist required by T040.

assignment:
  id: 696-frontend-4
  ado_task: 821
  spec_tasks: [T040]

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality
  expected_head: 6a7c259a3115e5bfbe637cf6776d67650e49dbf6

worker: frontend-engineer

objective: >
  Close CR-003 state only: incorporate the user's browser validation evidence, correct the stale
  implementation commit reference, mark T040 complete, create a valid traceable closure commit,
  and update ADO Task #821. No product-code change is authorized unless a state-only correction
  cannot be completed without it, in which case return BLOCKED.

acceptance_criteria:
  - Verify branch, expected HEAD and tracked cleanliness before writes.
  - Update repository-local IMPLEMENTATION-CHECKPOINT.md: record the user's 2026-10-20 npm-run-dev browser confirmation as the manual T040 evidence; replace stale implementation SHA d9ee4e7 with 6a7c259; distinguish worker command evidence from user browser evidence.
  - Mark T040 [x] in repository-local tasks.md; do not alter global orchestration artifacts.
  - Create a new closure commit (do not rewrite 6a7c259) containing only the state corrections, with real newline-separated message text and a trailer parsed by `git interpret-trailers --parse` exactly `Refs: #696 #821`.
  - Add a progress/completion comment to ADO Task #821 describing T039/T040 evidence and the closure commit; read it back before claiming success. Do not close the Task unless repository merge policy independently calls for it.
  - Preserve all known untracked files; explicit staging only; no product-code changes, push, PR or deploy.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```

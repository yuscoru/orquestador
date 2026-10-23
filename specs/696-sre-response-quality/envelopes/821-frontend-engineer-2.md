# Task Envelope — 821 — frontend-engineer — CR-003 Evolution drawer (F2)

Issued 2026-10-20 by the admiral. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: CHANGE
change_request: CR-003
feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality
  change: changes/CR-003.md
  issue: issues/ISS-005.md
  specification: spec-frontend.md
  plan: plan-frontend.md
  tasks: tasks.md

assignment:
  id: 696-frontend-3
  ado_task: 821
  spec_tasks: [T039, T040]

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality
  expected_head: 91f49bb9aa0e93d76164dab836d5330f400a8106

worker: frontend-engineer

objective: >
  Apply approved CR-003: move the existing Quality Evolution content from the inline area below
  the catalog into a Quality-specific right-side modal drawer over the catalog, reusing the shared
  Dialog/drawer pattern while preserving all data, authorization and rendering semantics.

acceptance_criteria:
  - Re-project the CR-003 delta into the repository-local specs/696-sre-response-quality artifacts, preserving global ids T039-T040 and completed prior work.
  - T039 exactly as approved in global tasks.md: shared Dialog primitive; right-side full-height overlay; no reuse of the PlaybookEditorDrawer component; complete Evolution states/chart/table moved; selection opens; close control/Escape/outside click close and clear selection; accessible title/description; contained vertical/horizontal overflow; no inline duplicate; no API/type/RBAC change.
  - T040 exactly as approved in global tasks.md: lint no worse than recorded baseline, build passes, and manual desktop/narrow-viewport interaction/state checklist is evidenced in IMPLEMENTATION-CHECKPOINT.md.
  - Repository instructions and constitution prevail. Do not weaken an acceptance criterion; return BLOCKED if one cannot be validated.

contracts:
  consumes:
    - name: quality-read-api (C-01 R1+R2+R5)
      change: none
    - name: quality.view (C-02)
      change: none
  provides: []

constraints:
  - Before writes, verify repository, branch and expected HEAD. If tracked changes or unexpected divergence exist, stop and return BLOCKED; known untracked .github/, .specify/, .vscode/ and AGENTS.md are pre-existing and outside scope except the explicit local spec projection required above.
  - Do not edit soarplus-api or soarplus-agentics.
  - No new runtime dependency and no test framework introduction.
  - Stage explicit paths only; never git add -A or git add .
  - Commit trailer: "Refs: #696 #821".
  - Report code written, validations executed/passed, local state/checkpoint, commit, ADO update, push and PR as separate facts.

delivery:
  update_ado: true
  commit: true
  push: false
  create_pr: false
  deploy: false
```

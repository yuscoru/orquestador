# Delivery Envelope — frontend-engineer — frontend branch push (F4)

Issued 2026-10-20 by the admiral after explicit user Gate 4 authorization. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: DELIVERY
feature:
  ado_user_story: 696
  slug: sre-response-quality

assignment:
  id: 696-frontend-5
  ado_task: 821
  spec_tasks: []

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality
  expected_head: 0032c688ff7db894e96c3d0a441c75334a40241f
  remote: origin

worker: frontend-engineer

objective: >
  Push the existing frontend feature branch at exactly the expected HEAD to origin and verify the
  remote branch. This envelope authorizes delivery only; it authorizes no code, state, commit,
  rebase, merge, force-push, PR or deployment operation.

preconditions:
  - Verify repository path, branch and exact expected HEAD.
  - Verify tracked tree is clean. Known untracked `.github/`, `.specify/`, `.vscode/`, `AGENTS.md` must remain untouched and unpushed.
  - Do not pull, fetch-and-merge, rebase, amend, create a commit or alter credentials/configuration persistently.

steps:
  - Push `feature/696-sre-response-quality` to `origin` without force.
  - Verify by remote read-back that `refs/heads/feature/696-sre-response-quality` resolves exactly to `0032c688ff7db894e96c3d0a441c75334a40241f`.
  - Report local HEAD, remote SHA, ahead/behind if available, and whether the push created or updated the branch.
  - If authentication/credential resolution fails, return BLOCKED without changing git configuration or embedding/reporting credentials.

delivery:
  update_ado: false
  commit: false
  push: true
  create_pr: false
  deploy: false
```

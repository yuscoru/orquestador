# Operational Envelope — frontend-engineer — ignore Next cache symlink (F6)

Issued 2026-10-21 by the admiral after explicit user authorization. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: OPERATIONS_CLOSURE
feature:
  ado_user_story: 696
  slug: sre-response-quality

assignment:
  id: 696-frontend-7
  ado_task: 821
  spec_tasks: []

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality
  expected_head: 0032c688ff7db894e96c3d0a441c75334a40241f

worker: frontend-engineer

objective: >
  Add the exact local-only ignore entry `/.next` to `.git/info/exclude` so the authorized `.next`
  symlink is not reported or accidentally staged, then verify and close F5 operationally.

preconditions:
  - Verify repository, branch and exact HEAD.
  - Verify `.next` is still the exact symlink to `/tmp/soarplus-frontend-next` and the target is writable.
  - Verify tracked tree clean and current untracked inventory consists of the known paths plus `.next`.

steps:
  - Idempotently append exactly `/.next` to `.git/info/exclude` only if no exact line exists.
  - Verify the exact line occurs once.
  - Verify `git check-ignore -v .next` cites `.git/info/exclude` and `git status --short` no longer lists `.next`.
  - Verify known untracked files remain, nothing is staged, HEAD is unchanged and the link/target are unchanged.

constraints:
  - No tracked file, source, specification, dependency or Git configuration outside `.git/info/exclude` may change.
  - Do not run npm/build/dev; do not delete or recreate the link/target.
  - Do not commit, push, update ADO, create a PR or deploy.

delivery:
  update_ado: false
  commit: false
  push: false
  create_pr: false
  deploy: false
```

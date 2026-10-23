# Operational Envelope — frontend-engineer — externalize Next cache (F5)

Issued 2026-10-20 by the admiral after explicit user authorization. Immutable once sent.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT
kind: OPERATIONS
feature:
  ado_user_story: 696
  slug: sre-response-quality

assignment:
  id: 696-frontend-6
  ado_task: 821
  spec_tasks: []

repository:
  name: soarplus-frontend-app1
  path: /root/soarplus-frontend-app1
  branch: feature/696-sre-response-quality
  expected_head: 0032c688ff7db894e96c3d0a441c75334a40241f

worker: frontend-engineer

objective: >
  Create the operational Next.js cache target `/tmp/soarplus-frontend-next` and make repository
  path `.next` a symbolic link to that exact target, so generated Next artifacts use the large
  ephemeral overlay instead of the small persistent `/root` volume.

preconditions:
  - Verify repository, branch, exact HEAD and tracked cleanliness.
  - Verify `.next` is absent. If it exists as any file, directory or link, return BLOCKED; do not remove or replace it.

steps:
  - Run `mkdir -p /tmp/soarplus-frontend-next`.
  - Run `ln -s /tmp/soarplus-frontend-next /root/soarplus-frontend-app1/.next`.
  - Verify `.next` is a symlink, `readlink` is exactly `/tmp/soarplus-frontend-next`, target is a writable directory, and both paths resolve to the overlay target rather than consuming `/root` blocks.
  - Verify Git tracked state and the known untracked inventory are unchanged; `.next` must remain ignored/not staged.
  - Do not run npm, Next, build or dev; do not delete cache contents.

constraints:
  - This is an operational filesystem action only. No source, specification, checkpoint, Git config or dependency change.
  - Do not commit, push, create a PR, update ADO or deploy.
  - Report before/after `df` for `/root` and `/tmp` and exact link verification.

delivery:
  update_ado: false
  commit: false
  push: false
  create_pr: false
  deploy: false
```

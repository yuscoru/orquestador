# Operational Envelope — frontend — start local Quality UI (F7)

Issued after Q1 API verification following pod recreation.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-frontend-11, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-frontend-app1, path: /root/soarplus-frontend-app1, branch: feature/696-sre-response-quality, expected_head: 0032c688ff7db894e96c3d0a441c75334a40241f}
objective: Recreate the external Next cache target and start frontend against the audited Quality API on 127.0.0.1:8000.
acceptance_criteria:
  - Verify no listener/process on 3000; branch/HEAD/tracked state unchanged; persistent `.next` exact symlink and local ignore intact.
  - Recreate `/tmp/soarplus-frontend-next`, verify writable overlay target, and clean only its contents if needed; never remove `.next`.
  - Export repo node_modules first in `NODE_PATH` exactly as corrected runbook requires and start from checkout with `NEXT_PUBLIC_ENDPOINT=http://127.0.0.1:8000 npm run dev` in background; persist PID/log in `/tmp`.
  - Verify process/listener 3000, GET / returns 200, compile succeeds, and log has no `Cannot find module`, PostCSS error, ERROR or 500 after request.
  - Verify API health/Quality remains reachable; do not inject browser localStorage (user does that in browser).
  - No source/Git/config/dependency changes, npm install, build, commit, push, ADO, PR or deploy.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```
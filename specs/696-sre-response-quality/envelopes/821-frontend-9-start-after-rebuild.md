# Operational Envelope — Frontend — rebuild/start local UI (F9)

Issued after A5 SystemDevAgent and Q2 read-only API verified following pod recreation.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-frontend-15, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-frontend-app1, path: /root/soarplus-frontend-app1, branch: feature/696-sre-response-quality, expected_head: 73f8812a99234341a67d0552831bdc26b50d056c}
objective: Recreate /tmp Next cache and start local frontend on 3000 against verified read-only API 8000.
acceptance_criteria:
  - Verify API health 200 before start; no listener 3000; persistent `.next` symlink remains.
  - Recreate only `/tmp/soarplus-frontend-next`; set NODE_PATH to repo node_modules; start `NEXT_PUBLIC_ENDPOINT=http://127.0.0.1:8000 npm run dev` in background with PID/log under /tmp.
  - Verify listener 3000, `/` and `/quality` 200, compile success and no module/PostCSS/error/500 log.
  - No localStorage injection, install, repo/source/config/dependency change, commit, push, PR, ADO or deploy.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```

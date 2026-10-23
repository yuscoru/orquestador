# Operational Envelope — agentics — rebuild/start SystemDevAgent (A2)

Issued after explicit user request following pod recreation.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-agentics-10, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-agentics, path: /root/soarplus-agentics, branch: feature/696-sre-response-quality, expected_head: 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f}
objective: Rebuild the validated temporary runner/venv after pod recreation and start SystemDevAgent for hybrid DEV operation.
acceptance_criteria:
  - Verify no listener/process on 8080 and persistent repo state unchanged before writes.
  - Rebuild `/tmp/sre-runner-source-096ac69f2a9d` and `/tmp/sre-system-dev-venv` exactly per corrected runbook §4; validate runner metadata/imports and non-serving preflight only as documented.
  - Start in background with the temporary Python and `dev_pod.py --serve --user-judge-key --api-authorization-verified`; do not use placeholder OPENAI_API_KEY for serve.
  - Persist PID and sanitized log under `/tmp`; verify PID alive, listener 8080, localhost AgentCard and Service-DNS AgentCard both 200 with name SystemDevAgent/url dev-jcorujo-agent.
  - Do not invoke/evaluate a target and do not access/write DB directly.
  - No repository/ref/config changes, deletions, commit, push, ADO, PR or deploy.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```
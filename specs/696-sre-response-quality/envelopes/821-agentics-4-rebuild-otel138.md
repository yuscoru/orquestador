# Operational Envelope — agentics — clean OTEL 1.38 runtime and standard restart (A4)

Issued after explicit user authorization. Implements the operational remedy for ISS-006 only; it does not authorize any A2A task or evaluation.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
issue: ISS-006
assignment: {id: 696-agentics-15, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-agentics, path: /root/soarplus-agentics, branch: feature/696-sre-response-quality, expected_head: 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f}
objective: Build a fresh parallel temporary runtime with a coherent OpenTelemetry 1.38 family, then replace PID 42557 only after fail-closed validation.
acceptance_criteria:
  - Prove current PID 42557 exact standard command/alive and existing API/frontend health. Do not touch it if parallel build/validation fails.
  - Create a new uniquely named `/tmp` venv; retain `/tmp/sre-system-dev-venv` unchanged for rollback and reuse only the already validated runner source/commit as read-only input.
  - Reproduce the validated runner 0.1.2 commit `096ac69f2a9d20621f608c610d5f7b192cc15285` and ADK-compatible layering, but explicitly install `opentelemetry-exporter-otlp-proto-http==1.38.0` and `opentelemetry-exporter-otlp-proto-grpc==1.38.0`; prevent/remove the incompatible 1.45.1/0.66b1 family in the new venv. No site-packages patch.
  - Fail closed unless `pip check` passes; exact grpc/http/sdk/api/proto/proto-common metadata is coherent at 1.38.0 and incompatible OTEL remnants absent; Guardrails, runner, Google ADK, A2A and HTTP exporter imports pass; importing LogRecord succeeds while absence of ReadableLogRecord from SDK 1.38 is explicitly expected; non-serving `check_eval_runtime.py`/dev_pod preflight passes.
  - Use only the user-approved rotated OPENAI_API_KEY from exact root:root 0600 `agents/whois-agent/.env`, without output/hash/length/argv/generated-secret; load only that variable.
  - After all build gates pass, TERM exact PID 42557 and wait for listener gone; start standard in-process from new venv with `EVAL_SCAN=1000`, `EVAL_SAMPLE_SIZE=5`, `dev_pod.py --serve --api-authorization-verified`; omit user-judge/manual flags.
  - Verify PID/env-presence/argv/listener and local + Service-DNS AgentCards with GET only; verify API 8000 and frontend 3000 remain healthy. If new serve fails, stop it and restore the old standard process from retained venv using the same approved key/settings.
  - Record built-in runner index assurance accurately. Do not POST, create a non-eval task, invoke or evaluate.
  - No repository/ref/config/dependency file change, commit, push, ADO, PR or deploy. Do not delete old venv/runtime/source.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```

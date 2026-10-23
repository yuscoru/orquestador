# Operational Result — ISS-006 clean OTEL 1.38 rebuild A4

Received from `agentics@soarplus` for `696-agentics-15`.

Status: COMPLETED. Fresh parallel venv `/tmp/sre-system-dev-venv-a4-otel138`; runner 0.1.2 at exact commit `096ac69f2a9d20621f608c610d5f7b192cc15285`. OTLP gRPC/HTTP, SDK/API/proto/proto-common all 1.38.0; semantic conventions 0.59b0; packaging 26.3 added explicitly after clean-runtime preflight exposed it missing. Incompatible 1.45.1/0.66b1 family absent. `uv pip check` passed across 268 packages. Guardrails, runner, ADK, A2A, HTTP exporter and LogRecord imports passed; ReadableLogRecord absence is expected under SDK 1.38. Non-serving dev_pod preflight passed.

Only after validation, exact old PID 42557 received TERM and lost its listener; it remains a PID-1 zombie without socket. New standard PID `47862` uses the new venv with exact `dev_pod.py --serve --api-authorization-verified`, no worker/manual flags, OPENAI_API_KEY present without disclosure, EVAL_SCAN=1000, EVAL_SAMPLE_SIZE=5. Listener 8080 and local/Service-DNS cards verified. API 8000 and frontend 3000/Quality remained 200. Old venv retained for rollback. Built-in runner index assurance reported existing unchanged indexes.

Admiral independently verified PID/argv/env-presence/listener, complete metadata matrix, imports, `uv pip check`, both cards, API/frontend, new log without import/error traceback, expected repository state, and old zombie/no listener. No POST/task/evaluation, source/ref/dependency-file change, commit, push, ADO, PR or deployment.

ISS-006 runtime symptom is remediated; only a separately authorized minimal evaluation can prove end-to-end SRE execution and `adk_events` accounting.

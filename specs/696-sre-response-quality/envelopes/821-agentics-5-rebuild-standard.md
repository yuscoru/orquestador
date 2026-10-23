# Operational Envelope — Agentics — rebuild standard SystemDevAgent (A5)

User explicitly requested full local stack restart after temporary `/tmp` runtime disappeared.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-agentics-22, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-agentics, path: /root/soarplus-agentics, branch: feature/696-sre-response-quality, expected_head: 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f}
objective: Rebuild validated OTEL 1.38 runtime and start standard in-process SystemDevAgent on 8080.
acceptance_criteria:
  - Rebuild fresh parallel `/tmp/sre-system-dev-venv-a5-otel138` from runner 0.1.2 exact commit `096ac69f2a9d20621f608c610d5f7b192cc15285`; explicitly coherent OTEL 1.38 grpc/http/sdk/api/proto/proto-common and packaging; preserve no old runtime assumption.
  - Fail closed on `uv pip check`, metadata/imports, Guardrails/ADK/A2A/HTTP and non-serving preflight.
  - Use approved rotated OPENAI_API_KEY from root:root 0600 whois-agent env without output/hash/argv/generated secret; load only key.
  - Start standard command with EVAL_SCAN=1000/EVAL_SAMPLE_SIZE=5, `--serve --api-authorization-verified`, omitting worker/manual flags; PID/log under `/tmp`.
  - Verify PID/listener 8080 and local/Service-DNS AgentCards via GET; no POST/evaluation/DB direct command.
  - No repo/config/versioned changes, commit, push, PR, deploy or ADO.
```

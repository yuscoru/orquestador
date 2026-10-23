# Operational Envelope — agentics — restart standard in-process SystemDevAgent (A3)

Issued after user correction and explicit confirmation that the approved key in `agents/whois-agent/.env` was rotated. Admiral observed the key variable nonempty without reading/outputting it, but observed mode 0644 despite the user's statement that it was 0600; fail closed and correct/verify mode before reading.

```yaml
mode: IMPLEMENT
kind: OPERATIONS
feature: 696-sre-response-quality
assignment: {id: 696-agentics-12, ado_task: 821, spec_tasks: []}
repository: {name: soarplus-agentics, path: /root/soarplus-agentics, branch: feature/696-sre-response-quality, expected_head: 5e720a3ebb2ebc766943e4dc45ca1af4b43c9b1f}
objective: Replace PID 37673 child-worker mode with standard in-process SystemDevAgent so evaluation usage can flow through ADK accounting.
acceptance_criteria:
  - Prove exact current PID/cmd and no active evaluation; fail closed if unexpected.
  - Set exact file `/root/soarplus-agentics/agents/whois-agent/.env` to owner-root mode 0600 and verify a nonempty OPENAI_API_KEY without printing/logging/hash/length/value; user confirms this is rotated and approved.
  - Load only OPENAI_API_KEY from that file through a non-logging parser/exec wrapper; do not source/export other .env variables and do not place the value in argv, logs or generated files.
  - TERM exact PID from `/tmp/sre-system-dev.pid`, wait/reap, prove PID and listener 8080 gone before replacement.
  - Start with `EVAL_SCAN=1000`, `EVAL_SAMPLE_SIZE=5`, `/tmp/sre-system-dev-venv/bin/python dev_pod.py --serve --api-authorization-verified`; omit both `--user-judge-key` and `--manual-dev-pilot`. Background process, PID/raw/sanitized logs under `/tmp`.
  - Verify PID alive, process environment presence only for OPENAI_API_KEY/EVAL vars, cmdline exact without worker flags, listener 8080, local and Service-DNS cards 200/name/url/protocol, and API/frontend processes remain alive.
  - Do not POST/invoke/evaluate. Record any built-in runner DB commands accurately.
  - No source/ref/config/dependency changes except approved chmod on the existing untracked secret file; no commit, push, ADO, PR or deploy.
delivery: {update_ado: false, commit: false, push: false, create_pr: false, deploy: false}
```

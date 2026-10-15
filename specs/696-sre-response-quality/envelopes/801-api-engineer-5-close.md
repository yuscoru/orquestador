# Task Envelope — 801 — api-engineer — E5-close (closure of slice 5)

Issued 2026-10-15 by the admiral. Immutable once sent.

Slice note: envelope E5 (`envelopes/801-api-engineer-5.md`, T022-T026) was issued and the session was interrupted before
the worker returned a Task Result. The admiral and the captain observed afterwards, read-only, that soarplus-api holds
commits b4164e1 (OpenAPI contract test, access matrix, README) and d8faac3 (final checkpoint, T022-T026 marked complete),
both with trailer `Refs: #696 #801`, and that ADO Task #801 has NO comment for E5 (last comment is the E4 one, id 18097197,
2026-10-15T20:51Z). This envelope closes that gap. It authorizes NO code change.

```yaml
protocol_version: "1.0"

mode: IMPLEMENT

feature:
  ado_user_story: 696
  slug: sre-response-quality

source:
  artifacts: /root/soarplus-dev-orchestration/specs/696-sre-response-quality

assignment:
  ado_task: 801
  spec_tasks:
    - T022
    - T023
    - T024
    - T025
    - T026

repository:
  name: soarplus-api
  path: /root/soarplus-api
  branch: feature/696-sre-response-quality

worker: api-engineer

objective: >
  Close envelope E5 honestly. First establish, from your own repository evidence, whether E5 (T022-T026, see
  envelopes/801-api-engineer-5.md) was already fully completed and validated, lacking only its Azure DevOps comment and
  its Task Result. If it was, publish the E5 comment on ADO Task #801, confirm it by reading it back, and return the
  canonical Task Result for E5 as your final message so the admiral can store it. If it was not, do not publish
  anything, do not complete the work silently, and say precisely what is missing.

acceptance_criteria:
  - Step 1 (verify, no writes) - read the E5 envelope and verify each of its acceptance criteria against the repository as it is now, with evidence (commit, path, test output): T022 contract test, T023 access matrix, T024 documentation, T025 full-suite run with the comparison against the 5 recorded baseline failures and the isolation check at 580a532, T026 final checkpoint with the cassdk assessment, the accepted risk and the not-verified list. Re-run the two new test modules and the full unit suite yourself; do not copy the counts from the checkpoint.
  - Step 1 also confirms the negative constraints of E5 - GET /db/collections* untouched, no index created on agent_eval_results and no write to it, no push, no pull request, Task #801 still Active, the pre-existing uncommitted files not staged or committed by b4164e1 or d8faac3.
  - State explicitly whether E5 was already closed apart from the ADO comment and the Task Result. The answer is one of - YES, closed apart from those two artifacts; NO, with the list of what is missing or defective. Do not answer YES unless every criterion above has evidence.
  - Step 2 (only if the answer is YES) - publish ONE comment on ADO Task #801 summarizing E5: tasks T022-T026, commits b4164e1 and d8faac3 on feature/696-sre-response-quality (local, not pushed), the test evidence you re-ran, what is not verified (live DocumentDB behaviour, writer indexes, Python 3.13, custom roles, consumers), the cassdk assessment, and that the Task stays Active. Read the comment back from ADO and report its id and creation time. A comment you could not read back is not confirmed.
  - The Task Result is for E5 as a whole (spec_tasks T022-T026, commits b4164e1 and d8faac3), written in the canonical structure of protocols/task-result.md, with PASS / FAIL / NOT_VERIFIED and evidence per acceptance criterion of E5. State in its summary that the original E5 invocation was interrupted and that this result was produced by the closure envelope E5-close, and distinguish what you re-verified now from what you took from the checkpoint.
  - The Task Result reports the ADO outcome as requested / confirmed / assumed, separately, and the Git state (commits, pushed false).
  - If Step 1 finds a defect or a gap, return PARTIAL or a Blocker Result per protocols, with the exact remaining work. Do not fix code under this envelope; a fix needs its own envelope.

contracts:
  consumes: []
  provides:
    - name: quality-read-api
      consumer: soarplus-frontend-app1
      reference: /root/soarplus-dev-orchestration/specs/696-sre-response-quality/contracts.md#c-01-quality-read-api

dependencies: []

constraints:
  - No change to any file of soarplus-api. No commit is expected. If you find a change is unavoidable, stop and report it instead of making it.
  - Do not stage, modify, revert or commit the pre-existing uncommitted files (.gitignore, api/lib/agent_discovery.py, requirements.txt, tests/test_agent_registry_discovery.py, .agents/, .env.local.example, .github/, .specify/, .vscode/, AGENTS.md, scripts/run_local.sh).
  - Do not use git stash, checkout of files, worktree or reset. For the isolation check at 580a532 export with git archive to a temporary directory, run there, and delete the directory.
  - Do not push. Do not create a pull request. Do not touch any other repository. Do not change the state of ADO Task #801; it stays Active until merge.
  - ADO - use the Azure DevOps integration for organization ES-ECC-INNOVATION, project SOARPLUS, Task #801 only. An integration that returns null for Task #801 is not the right one; try the other before concluding ADO is unavailable. Never claim the comment was published unless you read it back.
  - Never reproduce secrets, tokens or credential-bearing remote URLs in the comment, the result or any output.
  - Always finish by returning a Task Result or a Blocker Result as your final message, in canonical structure.

validation_expectations:
  - Independent re-run of tests.test_quality_openapi_contract and tests.test_quality_access_matrix.
  - Independent re-run of the complete unit suite, with the failing ids compared against the 5 recorded baseline failures.
  - ADO comment read back with id and creation time.

delivery:
  update_ado: true
  commit: false
  push: false
  create_pr: false
  deploy: false
```

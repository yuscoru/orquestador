# Worker Task Result Protocol

## Purpose

A Task Result is the canonical completion report returned by a repository
worker after processing an authorized Task Envelope.

It provides the orchestration layer with a structured, evidence-based account
of what actually happened.

It is not a conversational summary.

The Admiral uses this result to determine the next workflow transition.

---

# Result states

Supported terminal states are:

```text
COMPLETED
PARTIAL
NO_CHANGES_REQUIRED
```

Blocking termination is not represented here.

A blocked worker MUST use the separate `Blocker Result` protocol.

---

## `COMPLETED`

Use when:

- the assigned repository work is complete;
- applicable acceptance criteria were satisfied;
- required validation was performed;
- required repository state was persisted;
- authorized delivery operations were attempted and their real outcome is
  accurately reported;
- no unresolved blocker prevents the assignment from progressing.

---

## `PARTIAL`

Use only when useful work was safely completed but the full assignment could
not be completed and the remaining condition is not appropriately classified
as an active blocker.

Typical cases:

- an explicitly optional validation could not be performed;
- an authorized delivery operation such as push was unavailable after local
  implementation completed;
- part of an assignment was intentionally deferred by the caller.

`PARTIAL` MUST include the remaining work and reason.

If another decision or dependency is required before continuing, use a
Blocker Result instead.

---

## `NO_CHANGES_REQUIRED`

Use when repository analysis during implementation establishes that the
assignment requires no repository modification.

The worker MUST provide evidence supporting that conclusion.

It MUST NOT fabricate a commit merely to satisfy the envelope.

---

# Canonical result

```yaml
protocol_version: "1.0"

status: COMPLETED

feature:
  ado_user_story: 812
  slug: new-capability

assignment:
  ado_task: 934
  spec_tasks:
    - T014
    - T015

repository:
  name: soarplus-api
  branch: feature/812-new-capability

worker: api-engineer

summary: >
  Added the new execution status to the existing API response model and
  controller flow while preserving the current endpoint contract.

changes:
  - path: api/models/...
    description: Extended the shared response model.
  - path: api/controllers/...
    description: Mapped the agent result to the new field.
  - path: tests/...
    description: Added focused regression coverage.

acceptance_criteria:
  - criterion: Existing clients remain backward compatible.
    status: PASS
    evidence: >
      Existing response fields and endpoint semantics were preserved.

  - criterion: Relevant repository tests pass.
    status: PASS
    evidence: >
      Focused unit suite completed successfully.

contracts:
  changed: false
  verified:
    - name: agent-execution-status
      status: PASS

validation:
  - name: focused-unit-tests
    command: python -m unittest ...
    status: PASS
    evidence: 12 tests passed.

repository_state:
  tasks_updated: true
  checkpoint_updated: true

ado:
  requested: true
  updated: true
  task_state: Active
  comment_added: true

git:
  commit:
    requested: true
    created: true
    hash: abc1234
  push:
    requested: true
    completed: true
  branch: feature/812-new-capability

pull_request:
  requested: false
  created: false

deployment:
  requested: false
  performed: false

remaining_work: []

risks: []

warnings: []
```

---

# FIX and CHANGE results

A result for an envelope with `assignment.kind` of `FIX` or `CHANGE` carries one
extra block. Everything else is unchanged.

```yaml
assignment:
  kind: FIX                      # echoed exactly as received
  issue_ref: issues/ISS-001.md
  ado_bug: 1234

regression:
  test: tests/test_xxx.py::TestYyy::test_zzz
  red_before_fix: PASS           # PASS | NOT_VERIFIED, with how it was observed
  green_after_fix: PASS
  evidence: >
    Failed with <message> against the unfixed code; passes now.
```

For `CHANGE`, `regression` is replaced by:

```yaml
delta_projection:
  local_artifacts_updated: [spec.md, plan.md, tasks.md]
  superseded_tasks_marked: [T012]
  new_tasks_completed: [T027, T028]
```

`red_before_fix` is `NOT_VERIFIED` when the test was written after the fix; say so.
A fix without a regression test is not `COMPLETED`.

The `ado` block reports the Bug or CR Task that was actually updated, confirmed
by read-back. Engineers do not create work items.

---

# Traceability

The result MUST preserve the identifiers from the Task Envelope:

```yaml
feature:
  ado_user_story: ...

assignment:
  ado_task: ...
  spec_tasks: ...

repository:
  name: ...

worker: ...
```

The worker MUST NOT silently rewrite orchestration identity.

`worker` MUST be echoed exactly as received and MUST match the identifier the
responding agent has registered in `worker-registry.md`.

---

# Summary

```yaml
summary: >
  ...
```

The summary describes the actual repository outcome.

It SHOULD answer:

- what changed;
- why;
- whether the requested objective was achieved.

It MUST NOT claim operations that are only intended or assumed.

---

# Changes

```yaml
changes:
  - path: ...
    description: ...
```

Only material changes relevant to the assignment SHOULD be listed.

Avoid dumping the entire git diff into the result.

For `NO_CHANGES_REQUIRED`:

```yaml
changes: []
```

---

# Acceptance criteria

Each relevant acceptance criterion MUST receive a status.

Supported values:

```text
PASS
FAIL
NOT_VERIFIED
NOT_APPLICABLE
```

Example:

```yaml
acceptance_criteria:
  - criterion: Existing clients remain backward compatible.
    status: NOT_VERIFIED
    evidence: >
      No consumer integration environment was available.
```

`NOT_VERIFIED` is not equivalent to `PASS`.

The worker MUST NOT infer success without evidence.

---

# Contracts

```yaml
contracts:
  changed: false
  verified: []
```

If a contract changed under explicit authorization:

```yaml
contracts:
  changed: true

  changes:
    - name: agent-status-api
      reference: contracts/api-agent-status.yaml
      compatibility: backward-compatible
      description: Added an optional response field.

  verified:
    - name: agent-status-api
      status: PASS
```

The result MUST accurately expose cross-repository contract changes so that
the orchestration layer can notify dependent repositories.

---

# Validation

Each validation entry SHOULD contain:

```yaml
- name: focused-unit-tests
  command: python -m unittest ...
  status: PASS
  evidence: 12 tests passed.
```

Supported statuses:

```text
PASS
FAIL
NOT_RUN
```

When `NOT_RUN`, provide a reason:

```yaml
- name: browser-validation
  status: NOT_RUN
  reason: Browser environment unavailable.
```

A worker MUST NOT convert a missing validation into a successful one.

---

# Repository state persistence

```yaml
repository_state:
  tasks_updated: true
  checkpoint_updated: true
```

These fields report whether durable feature state was updated according to
repository rules.

If an artifact does not apply:

```yaml
repository_state:
  tasks_updated: false
  checkpoint_updated: false
  reason: No local Spec Kit feature exists for this assignment.
```

Repository-specific feature-delivery rules determine when these updates are
mandatory.

---

# Azure DevOps result

```yaml
ado:
  requested: true
  updated: true
  task_state: Active
  comment_added: true
```

The worker MUST distinguish authorization from confirmed execution.

Example failure:

```yaml
ado:
  requested: true
  updated: false
  task_state: unknown
  comment_added: false
  error: Authentication failed.
```

The worker MUST NOT say that ADO was updated unless confirmed.

---

# Git result

```yaml
git:
  commit:
    requested: true
    created: true
    hash: abc1234

  push:
    requested: true
    completed: true

  branch: feature/812-new-capability
```

A commit hash MUST only be included when a commit was actually created and
observed.

A failed push is represented explicitly:

```yaml
git:
  commit:
    requested: true
    created: true
    hash: abc1234

  push:
    requested: true
    completed: false
    error: Authentication failed.
```

Do not expose credentials, tokens, credential-bearing remote URLs or other
secret material in errors.

---

# Pull request result

```yaml
pull_request:
  requested: false
  created: false
```

If explicitly authorized in a future workflow:

```yaml
pull_request:
  requested: true
  created: true
  id: 1234
```

The worker does not infer PR authorization from implementation authorization.

---

# Deployment result

```yaml
deployment:
  requested: false
  performed: false
```

Deployment MUST remain false unless explicitly authorized and confirmed.

---

# Remaining work

For `COMPLETED`:

```yaml
remaining_work: []
```

For `PARTIAL`:

```yaml
remaining_work:
  - >
    Push the existing commit after repository authentication is restored.
```

The result MUST make the next action unambiguous.

---

# Risks

Risks discovered during implementation that remain relevant are returned as:

```yaml
risks:
  - severity: MEDIUM
    description: >
      Existing consumers outside this workspace have not been integration
      tested against the extended response.
```

Supported severities:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

A currently blocking risk belongs in a Blocker Result instead.

---

# Warnings

Warnings contain non-blocking execution observations.

```yaml
warnings:
  - >
    The repository emitted a known non-fatal tooling warning during push.
```

Warnings MUST NOT contain credentials or sensitive configuration values.

---

# `NO_CHANGES_REQUIRED`

Example:

```yaml
protocol_version: "1.0"

status: NO_CHANGES_REQUIRED

feature:
  ado_user_story: 812
  slug: new-capability

assignment:
  ado_task: 934
  spec_tasks: []

repository:
  name: soarplus-api
  branch: feature/812-new-capability

worker: api-engineer

summary: >
  The final agent execution status contract remains compatible with the API's
  existing response model and no API behaviour changes are required.

changes: []

acceptance_criteria:
  - criterion: Existing API behaviour remains unchanged.
    status: PASS
    evidence: >
      The consumed fields and semantics remain identical.

contracts:
  changed: false
  verified:
    - name: agent-status-api
      status: PASS

validation: []

repository_state:
  tasks_updated: false
  checkpoint_updated: false

ado:
  requested: false
  updated: false

git:
  commit:
    requested: false
    created: false
  push:
    requested: false
    completed: false

pull_request:
  requested: false
  created: false

deployment:
  requested: false
  performed: false

remaining_work: []
risks: []
warnings: []
```

---

# Honesty requirements

The Task Result is an evidence record.

Therefore:

- intended work is not completed work;
- a local commit is not a successful push;
- an attempted ADO operation is not a confirmed update;
- an unexecuted test is not a passed test;
- a plausible contract is not a verified contract;
- code written is not sufficient evidence of feature completion;
- an inferred external state MUST NOT be reported as observed fact.

When uncertain, report the uncertainty explicitly.

---

# Completion invariant

A Task Result MUST give the Admiral enough information to determine one of
the following without rereading the worker conversation:

```text
continue workflow
request rework
run integration review
wait for external completion
or finish repository work
```

Any state that requires another technical or organizational decision before
work can proceed SHOULD instead be represented by a Blocker Result.
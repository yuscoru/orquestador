# Worker Blocker Result Protocol

## Purpose

A Blocker Result is the canonical response returned by a repository worker
when it cannot safely continue or complete an assigned operation without an
external decision, dependency, authorization, contract change or correction
to the orchestration state.

A blocker is not a generic error report.

It represents a condition that requires action outside the worker's current
authority or repository-local scope.

The Admiral receives the blocker and decides how the orchestration workflow
must continue.

---

# Core rule

A worker MUST stop the affected work and return a Blocker Result when
continuing would require it to:

- modify another repository without an explicit assignment;
- change a cross-repository contract without authorization;
- guess missing requirements or acceptance criteria;
- operate on the wrong repository, branch or feature;
- violate repository governance;
- perform an unauthorized deployment, PR or destructive operation;
- depend on an external component whose required state is unavailable;
- make an architecture decision owned by the Captain;
- fabricate unavailable data or implementation behaviour;
- bypass a security or quality gate;
- expand feature scope materially beyond the Task Envelope.

The worker MAY continue unrelated, independently safe work only when the
remaining work is clearly separable and doing so cannot hide or worsen the
blocker.

Any such partial work MUST be reported explicitly.

---

# Canonical result

```yaml
protocol_version: "1.0"

status: BLOCKED

feature:
  ado_user_story: 812
  slug: new-capability

assignment:
  ado_task: 934
  spec_tasks:
    - T014

repository:
  name: soarplus-api
  branch: feature/812-new-capability

worker: api-engineer

blocker:
  type: CONTRACT_CHANGE_REQUIRED
  severity: HIGH

  summary: >
    The endpoint requirement needs an execution status value that is not
    present in the contract currently provided by soarplus-agentics.

  reason: >
    Implementing the requested response shape would require inventing a value
    or depending on an undocumented agent output.

  owner: captain

  affected_repository:
    name: soarplus-agentics

  required_action: >
    Decide whether the agent execution status contract should be extended. If
    approved, assign the corresponding Agentics work before resuming the API
    task.

  resumable: true

evidence:
  - path: api/utils/models.py
    description: Current response model has no equivalent property.
  - path: api/controllers/execution.py
    description: Controller cannot derive the requested value from available data.
  - contract: contracts/agent-execution-status.yaml
    description: Current contract does not define the requested value.

work_completed:
  changes_made: false
  files: []

repository_state:
  tasks_updated: false
  checkpoint_updated: false

ado:
  requested: true
  updated: true
  task_state: Active
  comment_added: true

git:
  commit:
    created: false
  push:
    completed: false

next_step: >
  Return control to the Admiral so the contract dependency can be resolved.

warnings: []
```

---

# Status

A Blocker Result MUST use:

```yaml
status: BLOCKED
```

Do not use:

```text
FAILED
ERROR
WAITING
PAUSED
PARTIAL
```

for a condition that requires orchestration intervention.

`PARTIAL` belongs to the Task Result protocol.

---

# Blocker types

The worker MUST classify the blocker using one of the following canonical
types whenever possible.

```text
CONTRACT_CHANGE_REQUIRED
CONTRACT_MISMATCH
SPEC_INCONSISTENCY
DEPENDENCY_NOT_READY
WORKER_MISMATCH
REPOSITORY_MISMATCH
BRANCH_MISMATCH
FEATURE_MISMATCH
SCOPE_EXPANSION_REQUIRED
ARCHITECTURE_DECISION_REQUIRED
REQUIREMENT_AMBIGUITY
ACCEPTANCE_CRITERIA_MISSING
AUTHORIZATION_REQUIRED
PERMISSION_DENIED
SECURITY_VIOLATION
GOVERNANCE_CONFLICT
VALIDATION_BLOCKED
EXTERNAL_SERVICE_UNAVAILABLE
ADO_UNAVAILABLE
GIT_DELIVERY_BLOCKED
ENVIRONMENT_INVALID
IMPLEMENTATION_CONFLICT
UNKNOWN_BLOCKER
```

`UNKNOWN_BLOCKER` SHOULD be used only when no existing type fits without
distorting the problem.

New blocker types SHOULD be added to this protocol deliberately rather than
invented ad hoc by individual workers.

---

# Blocker type semantics

## `CONTRACT_CHANGE_REQUIRED`

Use when completing the assignment requires a deliberate change to an
existing cross-repository interface.

Examples:

- frontend requires a new API field;
- API requires a new A2A response property;
- a producer must change a schema consumed by another repository.

The worker MUST NOT perform the external contract change without authorization.

Typical owner:

```text
captain
```

followed by reassignment through the Admiral.

---

## `CONTRACT_MISMATCH`

Use when two existing implementations or declared contracts disagree.

Example:

```text
API expects:
status: string

Agentics currently provides:
state: enum
```

This differs from `CONTRACT_CHANGE_REQUIRED`.

`CONTRACT_MISMATCH` means an inconsistency already exists.

`CONTRACT_CHANGE_REQUIRED` means a new change is needed to satisfy the feature.

---

## `SPEC_INCONSISTENCY`

Use when the approved specification, plan or tasks contradict each other, a
contract, or the observed code, and the assignment cannot be completed without
choosing which one is right.

Example:

```text
spec.md FR-004 requires every evaluation of a target to be listed, while
contracts.md C-01 defines the catalog as valid measurement points only.
```

It also applies when a `FIX` turns out to require changing the spec or a
contract.

The worker MUST cite both sides of the inconsistency, by path and requirement id.
It MUST NOT pick one and implement it.

Typical owner:

```text
captain
```

who opens or amends a Change Request. See `change-and-issue.md`.

---

## `DEPENDENCY_NOT_READY`

Use when another component or repository must complete work before the current
assignment can safely continue.

Example:

```text
Frontend implementation depends on an API endpoint that has not yet been
implemented on the feature branch.
```

The blocker SHOULD identify the dependency and the condition that makes it
ready.

---

## `WORKER_MISMATCH`

Use when the request is not addressed to the receiving worker.

This covers:

- the `worker` field is absent;
- the `worker` value is not registered in `worker-registry.md`;
- the `worker` value identifies a different worker;
- the request mode does not match the worker's registered mode, for example a
  Task Envelope sent to an `-analyst` or an analysis request sent to an
  `-engineer`.

The worker MUST stop before performing the work, even when it is technically
capable of performing it.

Use `REPOSITORY_MISMATCH` instead when the worker is correct but the repository
target is not.

---

## `REPOSITORY_MISMATCH`

Use when the worker was invoked against a repository it does not own or the
filesystem target does not match the Task Envelope.

The worker MUST stop before modifying files.

---

## `BRANCH_MISMATCH`

Use when the active branch differs from the branch authorized in the Task
Envelope and the worker has not been explicitly authorized to create or
switch it.

Example:

```text
expected: feature/812-new-capability
actual: main
```

The worker MUST NOT silently implement on another branch.

---

## `FEATURE_MISMATCH`

Use when branch identity, Spec Kit directory or ADO User Story identity do
not consistently identify the same feature.

Example:

```text
branch: feature/812-new-capability
spec:   specs/815-new-capability
```

The worker MUST not choose one arbitrarily.

---

## `SCOPE_EXPANSION_REQUIRED`

Use when implementation requires materially broader work than authorized.

Examples:

- modifying another repository;
- adding a new subsystem;
- broad migration;
- unrelated refactor required to make progress;
- introducing infrastructure changes not present in the assignment.

Routine local implementation detail is not scope expansion.

---

## `ARCHITECTURE_DECISION_REQUIRED`

Use when more than one materially different architecture is viable and the
choice affects global design or other repositories.

The repository worker MAY explain options and trade-offs.

It MUST NOT silently choose a cross-repository architecture on behalf of the
Captain.

---

## `REQUIREMENT_AMBIGUITY`

Use when the requested behaviour cannot be determined safely from the global
specification, Task Envelope or repository feature artifacts.

The blocker SHOULD state the exact ambiguity.

Avoid generic statements such as:

```text
Requirements unclear.
```

Prefer:

```text
The specification does not define whether a deleted agent should return 404
or a tombstone response, and both behaviours affect API compatibility.
```

---

## `ACCEPTANCE_CRITERIA_MISSING`

Use when completion cannot be objectively validated because required
acceptance criteria are absent.

This SHOULD NOT be used merely because the worker would prefer more detailed
requirements.

---

## `AUTHORIZATION_REQUIRED`

Use when the technical operation is understood but falls outside the
authorization granted by the Task Envelope or repository rules.

Examples:

- create PR;
- deploy;
- modify protected boilerplate;
- update CODEOWNERS-governed configuration;
- run a destructive migration.

---

## `PERMISSION_DENIED`

Use when an authorized operation cannot be performed because the executing
identity lacks the required permission.

Examples:

- ADO denies work-item update;
- git push rejected by permissions;
- protected file or external resource denies access.

Do not confuse permission failure with lack of authorization from the
orchestration workflow.

---

## `SECURITY_VIOLATION`

Use when continuing would violate a repository or platform security rule.

Examples:

- credentials found in a proposed tracked file;
- implementation requires exposing secrets;
- unsafe user-controlled destination would introduce SSRF;
- an operation requires leaking a credential-bearing remote URL.

The worker MUST stop the unsafe portion immediately.

It MUST NOT reproduce discovered secret values in the Blocker Result.

---

## `GOVERNANCE_CONFLICT`

Use when the Task Envelope, global plan or requested implementation conflicts
with the target repository's constitution or other binding governance.

Example:

```text
The assignment requires modifying protected Agentics boilerplate, but the
repository constitution requires explicit technical-owner approval.
```

The conflict MUST be identified precisely.

---

## `VALIDATION_BLOCKED`

Use when required validation cannot be executed and that validation is
necessary before the assignment may truthfully be declared complete.

Examples:

- required test infrastructure unavailable;
- mandatory build cannot run because an internal dependency is inaccessible;
- required integration environment is unavailable.

If validation is optional, the worker MAY instead return `PARTIAL`.

---

## `EXTERNAL_SERVICE_UNAVAILABLE`

Use when a required external system is unavailable and the worker cannot
continue meaningfully.

Examples:

- required API unavailable;
- package registry unavailable;
- dependency service unavailable.

Temporary inconvenience alone does not necessarily justify blocking if local
work can continue independently.

---

## `ADO_UNAVAILABLE`

Use when an ADO-dependent operation required for the workflow cannot be
performed because Azure DevOps is unavailable, unreachable or authentication
cannot be established.

If implementation itself is complete, the worker MAY return a `PARTIAL`
Task Result instead when no decision is required and only delivery remains.

Use `BLOCKED` when workflow progression itself depends on the ADO operation.

---

## `GIT_DELIVERY_BLOCKED`

Use when required Git delivery cannot proceed after local work has been
completed.

Examples:

- push rejected;
- remote unavailable;
- repository cannot authenticate.

A local commit MUST NOT be reported as pushed.

Depending on workflow policy, this may alternatively produce a `PARTIAL`
Task Result if no orchestration decision is required.

---

## `ENVIRONMENT_INVALID`

Use when the execution environment does not satisfy the repository's required
conditions.

Examples:

- required runtime missing;
- expected repository path not mounted;
- dependencies necessary for implementation cannot be resolved;
- required local toolchain unavailable.

The result SHOULD identify the missing condition without leaking credentials.

---

## `IMPLEMENTATION_CONFLICT`

Use when current repository state conflicts with the assumptions of the
authorized task.

Examples:

- another change has already modified the same design in an incompatible way;
- current feature code invalidates the expected implementation approach;
- a local checkpoint documents a newer implementation state incompatible with
  the Task Envelope.

This blocker SHOULD include repository evidence.

---

# Severity

Blockers MUST have one severity:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Severity describes impact, not urgency.

## `CRITICAL`

Use when the blocker involves:

- credential exposure;
- severe security risk;
- data loss or corruption risk;
- destructive production impact;
- fundamental architecture contradiction.

## `HIGH`

Use when:

- repository work cannot proceed;
- cross-repository contract resolution is required;
- architecture or authorization must be decided;
- required dependency is unavailable.

Most normal orchestration blockers will be `HIGH`.

## `MEDIUM`

Use when:

- progress can continue in other independent areas;
- only a bounded part of the assignment is blocked;
- the blocker materially affects validation or delivery but not implementation.

## `LOW`

Use sparingly.

A condition that does not actually block work belongs under `warnings` or
`risks`, not in a Blocker Result.

---

# Ownership

Every blocker SHOULD identify who must act next.

Supported logical owners are the worker identifiers registered in
`worker-registry.md`, plus the non-worker roles defined there:

```text
admiral
captain
reviewer
user
external
```

Do not maintain a second list of worker names here.

An owner MAY be an identifier listed in the registry as not yet registered,
when the work belongs to a repository that has no implementing agent. The
Admiral then routes it to a human.

Example:

```yaml
owner: captain
```

Meaning:

The blocker requires analysis or a cross-repository design decision.

Example:

```yaml
owner: api-engineer
```

Meaning:

Another repository must complete technical work before this worker can resume.

The Admiral remains responsible for routing the blocker.

The worker MUST NOT directly dispatch work to another worker unless the
orchestration protocol explicitly authorizes it.

---

# Affected repository

When another repository is involved:

```yaml
affected_repository:
  name: soarplus-api
```

When several repositories are involved:

```yaml
affected_repositories:
  - soarplus-api
  - soarplus-agentics
```

This field identifies impact.

It does not transfer ownership automatically.

---

# Required action

Every blocker MUST define a concrete condition for resolution.

Bad:

```yaml
required_action: Fix the API.
```

Good:

```yaml
required_action: >
  Decide whether the API response contract may add optional field
  execution_status. If approved, assign the API contract change before
  resuming the frontend task.
```

The required action SHOULD be sufficient for the Admiral to determine the
next workflow transition.

---

# Resumability

A blocker MUST state whether the current worker assignment can resume after
the condition is resolved.

```yaml
resumable: true
```

or:

```yaml
resumable: false
```

Use `false` when the assignment itself must be replaced, re-planned or
cancelled.

Example:

```yaml
resumable: false
```

when analysis establishes that the repository should no longer implement the
assigned responsibility.

---

# Evidence

A blocker SHOULD include enough evidence to justify stopping work.

```yaml
evidence:
  - path: src/lib/types.ts
    description: Current response type lacks the required property.
```

Evidence may reference:

- source files;
- tests;
- Spec Kit artifacts;
- repository instructions;
- schemas;
- contracts;
- observed command results;
- ADO operations;
- build or validation failures.

The worker MUST NOT include secret values.

Evidence should support the blocker, not dump unrelated diagnostic output.

---

# Work already completed

A worker may discover a blocker after performing some safe work.

That work MUST be disclosed.

Example:

```yaml
work_completed:
  changes_made: true

  files:
    - path: src/components/agent-status.tsx
      description: >
        Added UI state handling that does not depend on the unresolved field.

  validation:
    - name: npm run lint
      status: PASS
```

A blocker does not imply that nothing happened.

Conversely:

```yaml
work_completed:
  changes_made: false
  files: []
```

MUST be used when the worker stopped before modification.

---

# Persistence before blocking

When repository rules require durable state and safe changes have already
been made, the worker SHOULD update repository feature state before returning.

Example:

```yaml
repository_state:
  tasks_updated: false
  checkpoint_updated: true
```

The checkpoint SHOULD record:

- work completed;
- blocker;
- evidence;
- unresolved decision;
- next recommended action.

A blocked Spec Kit task MUST NOT be marked complete.

---

# Azure DevOps

The worker follows its repository's ADO policy and Task Envelope authorization.

Example:

```yaml
ado:
  requested: true
  updated: true
  task_state: Active
  comment_added: true
```

The Task SHOULD normally remain `Active` while blocked.

A blocker MUST NOT cause the worker to mark a Task `Closed`.

If the ADO update itself failed:

```yaml
ado:
  requested: true
  updated: false
  task_state: unknown
  comment_added: false
  error: Authentication unavailable.
```

Do not include credentials or sensitive connection values.

---

# Git state

If no commit was created:

```yaml
git:
  commit:
    created: false

  push:
    completed: false
```

If safe partial work was committed under explicit delivery authorization:

```yaml
git:
  commit:
    created: true
    hash: abc1234

  push:
    completed: true
```

A repository's own feature-delivery rules determine whether partial blocked
work should be committed.

The orchestration protocol does not force a commit merely because a blocker
exists.

---

# Cross-repository blocker routing

Workers MUST NOT negotiate cross-repository scope directly.

The normal route is:

```text
Worker
  |
  | Blocker Result
  v
Admiral
  |
  +--> Captain
  |      architecture / requirements / contract decision
  |
  +--> Another worker
  |      repository-local implementation
  |
  +--> Reviewer
  |      independent verification
  |
  +--> User / external dependency
         authorization or external action
```

Example:

```text
api-engineer
    |
    | CONTRACT_CHANGE_REQUIRED
    v
Admiral
    |
    v
Captain
    |
    | approves agent execution status contract change
    v
Admiral
    |
    v
agentics-engineer
    |
    | Task Result
    v
Admiral
    |
    v
api-engineer resumes
```

This preserves explicit orchestration ownership.

---

# Blocker vs risk

A **risk** is something that may cause a future problem.

A **blocker** prevents safe progression now.

Example risk:

```yaml
risks:
  - severity: MEDIUM
    description: >
      Existing external consumers may rely on undocumented behaviour.
```

Example blocker:

```yaml
blocker:
  type: CONTRACT_MISMATCH
  severity: HIGH
  summary: >
    Frontend and API currently define incompatible response schemas.
```

Do not create Blocker Results for ordinary risks.

---

# Blocker vs partial result

Use `PARTIAL` when:

- no decision is needed;
- remaining work is known;
- continuation is straightforward once an operational condition returns.

Use `BLOCKED` when:

- someone must decide;
- another repository must change;
- authorization is missing;
- scope must change;
- architecture must be resolved;
- the worker cannot safely infer what to do next.

Rule of thumb:

```text
"If the Admiral must route or decide something before I continue,
return BLOCKED."
```

---

# Security

Blocker diagnostics MUST obey repository security requirements.

In particular:

- never expose PATs;
- never expose API keys;
- never expose passwords;
- never print credential-bearing Git remote URLs;
- never paste raw environment variables containing secrets;
- never copy user tokens into the blocker;
- redact sensitive diagnostic output before persistence.

When the blocker concerns a discovered secret, identify the location and type
without repeating the value.

Example:

```yaml
blocker:
  type: SECURITY_VIOLATION
  severity: CRITICAL
  summary: >
    A tracked configuration file contains a credential-like value.

evidence:
  - path: agents/example-agent/.env
    description: >
      Credential-like value detected. Value intentionally omitted.
```

---

# Minimal blocker

When the situation is simple, a valid blocker may be compact:

```yaml
protocol_version: "1.0"

status: BLOCKED

feature:
  ado_user_story: 812

assignment:
  ado_task: 934

repository:
  name: soarplus-api

worker: api-engineer

blocker:
  type: BRANCH_MISMATCH
  severity: HIGH
  summary: >
    The active branch does not match the branch authorized by the task.
  reason: >
    Expected feature/812-new-capability but the repository is currently on
    main.
  owner: admiral
  required_action: >
    Prepare or authorize the expected feature branch.
  resumable: true

evidence:
  - description: Active Git branch is main.

work_completed:
  changes_made: false
  files: []

next_step: Return control to the Admiral.
```

---

# Completion invariant

A Blocker Result MUST allow the Admiral to determine, without rereading the
worker conversation:

1. what is blocked;
2. why it is blocked;
3. how severe it is;
4. which repository is affected;
5. whether any safe work was already completed;
6. who needs to act;
7. what exact action resolves the blocker;
8. whether the current worker can resume afterward.

A blocker that merely says:

```text
Cannot continue.
```

is invalid.
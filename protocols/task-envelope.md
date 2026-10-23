# Worker Task Envelope Protocol

## Purpose

A Task Envelope is the canonical instruction sent by the orchestration layer
to a repository worker when implementation work has been authorized.

It defines **what** the worker has been assigned.

It does not define **how** the repository implements the work.

Implementation rules remain owned by the target repository through its
constitution, `AGENTS.md`, Copilot instructions, scoped instructions,
Spec Kit artifacts and repository skills.

---

# Mode

Initial implementation supports:

```yaml
mode: IMPLEMENT
```

`IMPLEMENT` authorizes repository-local changes within the scope defined by
the Task Envelope.

Authorization to implement does not automatically authorize:

- changes to another product repository;
- scope expansion;
- deployment;
- feature-to-main pull requests;
- destructive infrastructure operations;
- undocumented contract changes.

Those actions require explicit authorization through the orchestration
workflow.

---

# Canonical envelope

```yaml
protocol_version: "1.0"

mode: IMPLEMENT

feature:
  ado_user_story: 812
  slug: new-capability

source:
  artifacts: /root/soarplus-dev-orchestration/specs/812-new-capability

assignment:
  kind: FEATURE
  ado_task: 934
  spec_tasks:
    - T014
    - T015

repository:
  name: soarplus-api
  path: /workspace/soarplus-api
  branch: feature/812-new-capability

worker: api-engineer

objective: >
  Expose the new agent execution status through the existing API surface.

acceptance_criteria:
  - Existing clients remain backward compatible.
  - The new status is represented by the shared API response model.
  - Authorization follows the repository's existing RBAC convention.
  - Relevant repository tests pass.

contracts:
  consumes:
    - name: agent-execution-status
      provider: soarplus-agentics
      reference: contracts/agent-execution-status.yaml

  provides:
    - name: agent-status-api
      consumer: soarplus-frontend-app1
      reference: contracts/api-agent-status.yaml

dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Required producer contract is available.

constraints:
  - no unrelated refactoring
  - preserve backward compatibility

validation_expectations:
  - repository-required unit tests
  - contract validation
  - RBAC validation

delivery:
  update_ado: true
  commit: true
  push: true
  create_pr: false
  deploy: false
```

---

# Identity

## `protocol_version`

Version of this orchestration contract.

Initial value:

```yaml
protocol_version: "1.0"
```

Workers MUST reject a protocol version they cannot interpret safely.

---

## `feature.ado_user_story`

Canonical global feature identifier.

This identity SHOULD remain consistent across affected repositories:

```text
ADO User Story : 812
Branch         : feature/812-new-capability
Global spec    : specs/812-new-capability/
Local spec     : specs/812-new-capability/
```

The worker MUST NOT silently substitute another feature.

---

## `feature.slug`

Canonical feature slug chosen by the orchestration workflow.

If existing repository state uses a different slug, the worker MUST report
the mismatch rather than rename or recreate artifacts automatically.

---

# Source

## `source.artifacts`

Absolute path to the feature's **global** artifacts in the orchestration
repository.

```yaml
source:
  artifacts: /root/soarplus-dev-orchestration/specs/812-new-capability
```

That directory contains the authoritative `spec.md`, `plan.md` and `tasks.md`
for the whole feature.

This field is **required**. The worker projects its repository-local
`spec.md`, `plan.md` and `tasks.md` from those files, as defined in
`workflow-state.md`. Without them `/speckit.implement` cannot run, because
`check-prerequisites.sh --require-tasks` aborts when they are missing.

The worker MUST read the path from this field and MUST NOT derive it from the
feature identity. Deriving a path is how a worker ends up projecting from the
wrong feature.

The path is **read-only** to the worker. Reading it is explicitly permitted
despite the orchestration repository being otherwise off limits.

If the path does not exist or does not contain the three files, stop and return
a blocker. Do not invent a local plan to proceed.

---

# Assignment

## `assignment.ado_task`

Azure DevOps Task assigned to this repository worker.

Example:

```yaml
ado_task: 934
```

The worker MUST NOT close or update unrelated Tasks.

---

## `assignment.spec_tasks`
Repository-local Spec Kit tasks covered by the assignment.

Example:

```yaml
spec_tasks:
  - T014
  - T015
```

This field MAY contain multiple local tasks when one ADO Task intentionally
groups them.

These ids come from the **global** `tasks.md` under `source.artifacts`. The
worker's projected `tasks.md` MUST keep them unchanged. Renumbering breaks the
thread between this field, the repository's tasks and the commit trailer.

The worker MUST NOT opportunistically complete unrelated Spec Kit tasks.

## `assignment.kind`

```yaml
kind: FEATURE | FIX | CHANGE
```

Optional; absent means `FEATURE`. `IMPLEMENT` remains the only `mode`: the kind
says **why** the work exists, not a new way of working. The full process is in
`change-and-issue.md`.

| Kind | Why | Required fields | `spec_tasks` |
|---|---|---|---|
| `FEATURE` | Approved plan | as above | the feature's task ids |
| `FIX` | Implementation does not meet the approved spec | `issue_ref`, `ado_bug`, `reproduction`, `expected` | empty |
| `CHANGE` | Approved Change Request | `change_ref`, `ado_task` of the CR Task | the CR's new ids |

```yaml
assignment:
  kind: FIX
  issue_ref: issues/ISS-001.md        # relative to source.artifacts
  ado_bug: 1234
  ado_task: null
  spec_tasks: []
  reproduction: >
    Steps or evidence that show the defect, without credentials or user data.
  expected: >
    Behaviour the spec requires, citing the requirement (e.g. FR-004).
```

```yaml
assignment:
  kind: CHANGE
  change_ref: changes/CR-001.md       # relative to source.artifacts
  ado_task: 1301
  spec_tasks: [T027, T028]
```

Rules by kind:

- `FIX` MUST include a regression test as an acceptance criterion: red before the
  fix, green after. It MUST NOT change a cross-repository contract or amend the
  spec. If the fix needs to, stop and return `SPEC_INCONSISTENCY` or
  `CONTRACT_CHANGE_REQUIRED`.
- `CHANGE` is accepted only if `change_ref` exists and carries the delta-gate
  record. A CR still in `DRAFT` is rejected with `AUTHORIZATION_REQUIRED`. The
  worker re-projects **only the delta** into its local `spec.md`, `plan.md` and
  `tasks.md`, keeping finished work and original ids.
- `FIX` and `CHANGE` use the commit trailer defined in `change-and-issue.md`:
  `Refs: #<US> #<bugId>` or `Refs: #<US> #<taskId>`.
- The branch is the feature branch while the feature is unmerged. The worker
  never invents another.

---

# Repository ownership

```yaml
repository:
  name: soarplus-api
  path: /workspace/soarplus-api
  branch: feature/812-new-capability
```

The worker MUST verify:

1. repository identity;
2. expected working path, when provided;
3. active branch;
4. branch-to-feature consistency;
5. local feature artifacts where applicable.

A mismatch is not automatically repairable.

If the worker cannot establish that it is operating on the intended
repository and feature, it MUST stop and return a blocker.

---

# Worker

```yaml
worker: api-engineer
```

The value MUST be an identifier registered in `worker-registry.md`. That
registry is the only source of truth for worker names, the repository each one
owns and the agent that implements it.

A Task Envelope MUST be addressed to an `-engineer` worker. `-analyst` workers
operate in `ANALYZE` mode only and MUST reject an envelope.

The receiving agent MUST verify that `worker` equals its own registered
identifier and that `repository.name` equals the repository registered for that
identifier.

A worker MUST NOT accept implementation ownership for another repository, and
MUST NOT accept an envelope addressed to a different worker even when it is
technically capable of performing the work.

Do not invent identifiers or display variants. An unregistered or absent worker
is a blocker.

---

# Objective

```yaml
objective: >
  Expose the new agent execution status through the existing API surface.
```

The objective states the repository-level outcome.

It SHOULD describe the required result rather than dictate low-level
implementation details.

The repository worker determines implementation mechanics according to local
architecture and rules.

---

# Acceptance criteria

```yaml
acceptance_criteria:
  - Existing clients remain backward compatible.
  - Relevant repository tests pass.
```

Acceptance criteria are mandatory implementation constraints.

The worker MUST:

- map them to repository implementation work;
- validate them where technically possible;
- report those that could not be verified.

The worker MUST NOT declare completion merely because code was written.

---

# Contracts

Contracts describe explicit cross-repository interfaces relevant to this
assignment.

```yaml
contracts:
  consumes: []
  provides: []
```

A contract entry SHOULD identify:

```yaml
- name: agent-execution-status
  provider: soarplus-agentics
  reference: contracts/agent-execution-status.yaml
```

or:

```yaml
- name: agent-status-api
  consumer: soarplus-frontend-app1
  reference: contracts/api-agent-status.yaml
```

The worker MUST NOT silently alter a cross-repository contract.

If implementation requires a contract change not authorized by the Task
Envelope, the worker MUST return a contract blocker.

---

# Dependencies

```yaml
dependencies:
  - repository: soarplus-agentics
    status: ready
    reason: Required producer contract is available.
```

Recommended dependency states:

```text
ready
pending
blocked
unknown
```

The worker MAY begin independent work when dependencies permit it.

It MUST NOT fabricate unavailable dependency behaviour merely to continue.

---

# Constraints

```yaml
constraints:
  - no unrelated refactoring
  - preserve backward compatibility
```

Constraints supplement repository rules.

They cannot override:

- repository constitution;
- security requirements;
- architecture invariants;
- explicit higher-authority repository instructions.

A conflicting Task Envelope MUST be rejected through a blocker instead of
silently violating repository governance.

---

# Validation expectations

```yaml
validation_expectations:
  - repository-required unit tests
  - contract validation
```

These are orchestration-level expectations.

They do not replace repository validation rules.

The worker MUST also execute any checks required by its own repository.

---

# Delivery authorization

Delivery actions are explicit:

```yaml
delivery:
  update_ado: true
  commit: true
  push: true
  create_pr: false
  deploy: false
```

`true` means the orchestration workflow authorizes the action if repository
rules and execution conditions permit it.

`false` means the worker MUST NOT perform that action.

Authorization does not imply success.

The worker MUST report exactly which operations were confirmed.

---

## Azure DevOps

When:

```yaml
update_ado: true
```

the worker follows the repository's delivery skill and ADO lifecycle rules.

The worker MUST NOT claim an ADO update unless the operation was confirmed.

---

## Commit

When:

```yaml
commit: true
```

the worker MAY create the repository commit after validation and persistence
requirements have been satisfied.

Commit format remains governed by repository rules.

For SOAR+ feature work the expected traceability convention is:

```text
Refs: #<US> #<taskId>
```

---

## Push

When:

```yaml
push: true
```

the worker MAY push the authorized branch.

A successful local commit is not evidence of a successful push.

---

## Pull request

When:

```yaml
create_pr: false
```

the worker MUST NOT create a PR.

PR lifecycle will normally be managed by the orchestration layer rather than
implicitly by repository workers.

---

## Deploy

When:

```yaml
deploy: false
```

the worker MUST NOT deploy.

Implementation permission and deployment permission are separate concerns.

---

# Repository-local execution

After accepting the envelope, the worker MUST transition into the target
repository's normal feature-delivery workflow.

Conceptually:

```text
Task Envelope
     |
     v
verify repository / branch / feature
     |
     v
load repository governance
     |
     v
restore local feature state
     |
     v
use repository feature-delivery workflow
     |
     v
implement
     |
     v
validate
     |
     v
persist tasks/checkpoint
     |
     v
perform authorized delivery actions
     |
     v
Task Result
```

The orchestration protocol deliberately does not duplicate repository-specific
implementation rules.

---

# Scope control

During implementation the worker MAY discover necessary work not present in
the envelope.

It MUST distinguish:

### Local implementation detail

A change that is required to complete the assigned objective and remains
inside the authorized repository and contract.

The worker MAY perform it.

### Scope expansion

A change that:

- affects another repository;
- changes an external contract;
- introduces materially new feature behaviour;
- changes architecture beyond the assignment;
- requires deployment or infrastructure authorization;
- contradicts the global plan or acceptance criteria.

The worker MUST stop the affected portion and return a blocker.

---

# Acceptance of the Task Envelope

Before modifying files, the worker MUST be able to establish:

- correct worker;
- correct repository;
- correct feature identity;
- correct branch or an explicitly authorized preparation state;
- understandable objective;
- sufficient acceptance criteria;
- no known blocking contract contradiction;
- no conflict with repository governance.

Otherwise it returns a blocker without pretending implementation has started.

---

# Completion

The Task Envelope itself is never the completion record.

On termination the worker MUST return exactly one of:

```text
Task Result
```

or:

```text
Blocker Result
```

A partial implementation that cannot safely continue MUST be represented
truthfully in one of those responses.
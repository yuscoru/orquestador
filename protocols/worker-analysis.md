# Worker Analysis Protocol

## Purpose

This protocol defines the contract used to ask a repository worker for
specialized analysis without modifying the repository.

It is primarily used by the **Captain** while preparing the global feature
specification and implementation plan.

The worker is the technical specialist for its repository. The Captain owns
the cross-repository analysis; the worker contributes repository-specific
facts, risks, contracts and implementation impact.

---

## Mode

```yaml
mode: ANALYZE
```

`ANALYZE` is strictly read-only.

A worker running in `ANALYZE` mode MUST NOT:

- modify files;
- create or switch branches;
- commit or push;
- modify Azure DevOps work items;
- create pull requests;
- update `tasks.md`;
- update `IMPLEMENTATION-CHECKPOINT.md`;
- perform destructive commands;
- claim that an implementation change has been made.

The worker MAY:

- inspect repository files;
- inspect git state;
- inspect existing specs and checkpoints;
- inspect tests and configuration;
- query read-only external sources when explicitly available and required;
- inspect other repositories for cross-repository context, provided it does
  not modify them.

---

## Request

The caller sends an analysis request with this logical structure:

```yaml
mode: ANALYZE

feature:
  ado_user_story: 812
  slug: new-capability

worker: api-analyst

repository:
  name: soarplus-api
  path: /workspace/soarplus-api

question: >
  Determine the impact of the feature on the API repository.

focus:
  - routes
  - controllers
  - models
  - RBAC
  - API contracts
  - cassdk
  - tests
  - cross-repository dependencies

constraints:
  modify_files: false
```

### Required fields

#### `mode`

MUST be:

```yaml
mode: ANALYZE
```

#### `feature.ado_user_story`

Canonical Azure DevOps User Story identifier for the global feature.

The worker MUST NOT invent or replace this identifier.

#### `worker`

Identifier of the worker the request is addressed to.

The value MUST be an identifier registered in `worker-registry.md`. That
registry is the only source of truth for worker names, the repository each one
owns and the agent that implements it.

An analysis request MUST be addressed to an `-analyst` worker. `-engineer`
workers operate in `IMPLEMENT` mode only and MUST reject an analysis request.

The receiving agent MUST verify that `worker` equals its own registered
identifier, and MUST NOT accept a request addressed to a different worker even
when it is technically capable of answering the question.

#### `repository.name`

Repository assigned to the worker.

The worker MUST verify that the repository it is analysing matches its own
declared ownership and the repository registered for its identifier.

#### `question`

The concrete question the worker must answer.

---

## Optional fields

### `feature.slug`

Human-readable feature slug.

When a branch or Spec Kit directory already exists, the worker SHOULD verify
that the slug is consistent with the repository state.

A mismatch MUST be reported rather than silently corrected.

### `repository.path`

Expected filesystem path.

If present, the worker SHOULD verify it before analysis.

### `focus`

Areas the caller wants examined in particular.

`focus` narrows attention but does not prevent the worker from reporting an
important impact outside the list.

### `constraints`

Additional execution constraints.

`modify_files: false` is implicit for `ANALYZE` and cannot be overridden.

---

# Repository target validation

Before loading repository context, the analyzer MUST verify that
`target_repository.path` is reachable and corresponds to
`target_repository.name`.

It MUST NOT silently analyze a different repository.

If the path is not reachable, return:

`BLOCKED / ENVIRONMENT_INVALID`

If the path is reachable but does not correspond to the expected repository,
return:

`BLOCKED / REPOSITORY_MISMATCH`

No repository analysis should continue until this validation succeeds.

---
# Repository context loading

Before answering, the worker MUST load the repository's local instructions.

The exact files vary by repository, but the normal precedence is:

1. repository constitution;
2. repository `AGENTS.md`;
3. project-wide Copilot instructions;
4. applicable scoped instructions;
5. relevant feature artifacts;
6. supporting repository documentation.

Repository-local authority remains authoritative for repository-specific
technical rules.

The orchestration repository MUST NOT duplicate those rules.

---

# Existing feature context

If the feature already exists locally, the worker SHOULD inspect, when
available:

```text
specs/<ADO-US>-<slug>/spec.md
specs/<ADO-US>-<slug>/IMPLEMENTATION-CHECKPOINT.md
specs/<ADO-US>-<slug>/tasks.md
specs/<ADO-US>-<slug>/plan.md
```

The worker MUST respect the repository's own semantics for those artifacts.

Unless local rules specify otherwise:

- `spec.md` describes required behaviour and acceptance criteria;
- `plan.md` describes the original implementation design;
- `tasks.md` describes executable work and progress;
- `IMPLEMENTATION-CHECKPOINT.md` describes current implementation reality.

The worker MUST distinguish current repository evidence from stale design.

---

# Analysis responsibilities

The worker SHOULD determine, where relevant:

1. whether the repository is affected;
2. affected components and files;
3. existing implementation that can be reused;
4. technical changes likely to be required;
5. contracts provided by this repository;
6. contracts consumed by this repository;
7. cross-repository dependencies;
8. compatibility constraints;
9. data model or schema impact;
10. security and authorization impact;
11. validation and testing requirements;
12. migration or deployment implications;
13. unresolved questions;
14. technical risks;
15. recommended repository-local scope.

The worker MUST prefer evidence from the repository over assumptions.

---

# Cross-repository analysis

A worker MAY inspect another repository when required to understand a contract
or dependency.

However:

- the worker remains responsible only for analysis of its own repository;
- it MUST NOT define implementation work for another repository as fact;
- it MUST distinguish observed facts from assumptions;
- unresolved cross-repository questions MUST be returned explicitly.

Example:

```yaml
dependencies:
  - repository: soarplus-agentics
    type: contract
    status: unresolved
    reason: >
      The API appears to consume an agent capability whose final response
      schema is not defined in this repository.
```

The Captain resolves the global architecture.

---

# Response

The worker returns a structured result.

```yaml
status: ANALYZED

feature:
  ado_user_story: 812
  slug: new-capability

repository:
  name: soarplus-api

affected: true

summary: >
  The feature requires changes to the API capability registry and one
  controller path. No database migration is currently evident.

affected_areas:
  - area: api/routes/...
    reason: New endpoint exposure.
  - area: api/controllers/...
    reason: Existing controller owns the relevant business operation.

existing_assets:
  - path: api/...
    relevance: Existing implementation can be extended.

contracts:
  provides:
    - name: agent-status-api
      type: REST
      status: existing
      impact: change-required

  consumes:
    - name: agent-status-result
      provider: soarplus-agentics
      type: application-contract
      status: requires-verification

dependencies:
  - repository: soarplus-agentics
    reason: API response depends on the result emitted by the agent.
    blocking: false

validation:
  required:
    - unit tests
    - RBAC verification
    - API contract validation

risks:
  - severity: HIGH
    description: >
      Changing the existing response model may affect current API consumers.

open_questions:
  - >
    Is the new field backward-compatible with the existing agent response?

recommended_local_scope:
  - Extend the existing response model.
  - Reuse the current controller path.
  - Add focused unit tests.

evidence:
  - path: api/...
    reason: Existing route definition.
  - path: tests/...
    reason: Current testing pattern.
```

---

# `affected`

`affected` MUST be explicitly returned.

Valid values:

```yaml
affected: true
```

or:

```yaml
affected: false
```

When `false`, the worker SHOULD explain why:

```yaml
affected: false

summary: >
  No frontend-visible behaviour or API contract consumed by this repository
  changes as part of the proposed feature.
```

`affected: false` is a technical conclusion, not permission to ignore an
uncertain dependency.

If impact cannot yet be established, return:

```yaml
affected: unknown
```

and explain the missing information under `open_questions`.

---

# Evidence

Important technical conclusions SHOULD reference repository evidence.

Evidence can include:

- source files;
- schemas;
- tests;
- configuration;
- existing specs;
- current checkpoints;
- documentation.

The worker MUST NOT fabricate paths or contracts.

---

# Risk severity

Use:

```text
CRITICAL
HIGH
MEDIUM
LOW
```

Meaning:

- `CRITICAL`: architecture, security, data integrity or delivery is blocked.
- `HIGH`: substantial implementation or compatibility risk.
- `MEDIUM`: meaningful concern that should be handled during implementation.
- `LOW`: limited impact or cleanup concern.

Risk severity is not the same as a blocker.

Blocking conditions are returned through the blocker protocol.

---

# Completion criteria

An `ANALYZE` request is complete when the worker has:

- loaded the applicable repository rules;
- inspected sufficient repository evidence;
- determined repository impact;
- identified relevant contracts and dependencies;
- identified material risks and unresolved questions;
- recommended repository-local scope;
- returned the structured analysis;
- made no repository or Azure DevOps modifications.
# SOARPLUS Orchestration Constitution

## Scope

This repository is the **orchestration layer** for multi-repository SOAR+ feature
development. It contains no product code.

Its binding rules live in `protocols/`, not here. This document is intentionally
minimal and exists to point there, so that no rule has two sources.

## Authority

```text
protocols/worker-registry.md    who exists, what they own, how they are named
protocols/workflow-state.md     where state lives, who writes each file
protocols/feature-branching.md  branch and feature identity across repositories
protocols/worker-analysis.md    ANALYZE request and response contract
protocols/task-envelope.md      IMPLEMENT assignment contract
protocols/task-result.md        result contract
protocols/blocker-result.md     blocker contract and canonical types
```

Agent behaviour is defined in `.github/agents/`. Those files are governed by the
protocols above.

## Core Principles

### I. No Second Source of Truth (NON-NEGOTIABLE)

Every fact has exactly one authoritative location.

Orchestration artifacts reference product-repository artifacts by path. They
never copy their content.

When orchestration state and a product repository disagree, the product
repository is authoritative about implementation and this repository is
authoritative about assignment.

### II. Orchestration Never Implements

No file in a product repository is modified from this repository.

Product changes are performed exclusively by the repository's registered
`-engineer`, under a Task Envelope.

### III. Durable State Over Chat

Anything required to resume work after a lost session is a committed file in
this repository, per `protocols/workflow-state.md`.

Chat history is not state.

### IV. Evidence Over Claims

A reported state requires observed evidence. One state never implies the next:
written is not validated, validated is not committed, committed is not pushed,
pushed is not merged, merged is not deployed.

### V. Zero Secrets

Artifacts in this repository are committed and shared. Secrets are referenced by
location and type, never reproduced.

## Governance

`protocols/` prevails over this document whenever they overlap. If a rule needs
to change, change the protocol.

Product repositories keep their own constitutions. This one does not override
them; a conflict between this layer and a repository's governance is resolved in
favour of the repository, and surfaced as a blocker.

**Version**: 1.0.0 | **Ratified**: 2026-10-14 | **Last Amended**: 2026-10-14

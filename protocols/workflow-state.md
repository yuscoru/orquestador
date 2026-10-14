# Workflow State Protocol

## Purpose

This protocol defines **where orchestration state lives on disk** and **who owns
each file**.

Chat context is lost when a session ends. Without a fixed layout, every session
invents its own and traceability is lost.

The rule is simple:

```text
If it must survive the session, it is a file in this repository.
```

---

# Scope boundary

This repository stores **orchestration** state: planning, assignment, routing
and results.

It does **not** store repository implementation state.

```text
soarplus-dev-orchestration     what was planned, assigned, answered, routed
<product repository>           what was actually implemented
```

Implementation reality remains owned by the product repository, in its own
`specs/<feature>/tasks.md` and `IMPLEMENTATION-CHECKPOINT.md`.

Orchestration artifacts **reference** those files. They never copy their
content.

Duplicating a checkpoint here creates a second source of truth that will drift
within days. When orchestration state and a product repository disagree, the
product repository is right about implementation and this repository is right
about assignment.

---

# Layout

```text
protocols/                       orchestration contracts, feature-independent
features/<ADO-US>-<slug>/        all state for one feature
```

The feature directory name uses the canonical feature identity defined in
`task-envelope.md`:

```text
features/696-sre-response-quality/
```

There is no index file. The directory listing is the index. A maintained list
of features would be a second source of truth.

## Feature directory

```text
features/<ADO-US>-<slug>/
    global-spec.md          captain    cross-repository behaviour and scope
    global-plan.md          captain    architecture, dependencies, sequencing
    contracts.md            captain    contract registry (references, not copies)
    handoff.md              captain    implementation-ready decomposition
    WORKFLOW-STATE.md       admiral    current execution reality
    log.md                  admiral    append-only chronological record
    envelopes/              admiral    issued Task Envelopes
    results/                admiral    received Task Results and Blocker Results
```

Not every file must exist from the start. Create each when it has content.

A feature directory containing only `global-spec.md` is a feature in
`PLANNING`. That is valid state, not an incomplete directory.

---

# File ownership

Two roles write to this repository. Ownership prevents collision.

| Path | Writer | Readers |
|---|---|---|
| `protocols/**` | human | everyone |
| `features/*/global-spec.md` | `captain` | everyone |
| `features/*/global-plan.md` | `captain` | everyone |
| `features/*/contracts.md` | `captain` | everyone |
| `features/*/handoff.md` | `captain` | `admiral` |
| `features/*/WORKFLOW-STATE.md` | `admiral` | everyone |
| `features/*/log.md` | `admiral` | everyone |
| `features/*/envelopes/**` | `admiral` | everyone |
| `features/*/results/**` | `admiral` | everyone |

The `captain` MUST NOT write execution state.

The `admiral` MUST NOT rewrite planning artifacts. When a plan is wrong, the
`admiral` routes the correction back to the `captain` rather than editing
`global-plan.md` directly.

Repository workers never write here. They write to their own repository and
return a protocol response; the `admiral` persists it.

---

# `WORKFLOW-STATE.md`

The single answer to "where is this feature right now".

Mutable. Overwritten as reality changes. Must be readable in under a minute.

```yaml
feature:
  ado_user_story: 696
  slug: sre-response-quality

phase: IMPLEMENTING

updated: 2026-10-14

repositories:
  - name: soarplus-agentics
    worker: agentics-engineer
    branch: feature/696-sre-response-quality
    status: IMPLEMENTING
    last_result: results/2026-10-13-agentics-engineer-934.md
    implementation_reality: >
      specs/696-sre-response-quality/IMPLEMENTATION-CHECKPOINT.md

active_blockers:
  - results/2026-10-13-api-engineer-941-blocker.md

pending_next_actions:
  - Await CAS account, capability and Secret provisioning.

delivery_authorizations_granted:
  create_pr: false
  deploy: false
```

Rules:

- `phase` uses the orchestration state model defined in the `admiral` agent;
- every repository listed MUST name a registered worker;
- `implementation_reality` is a **path reference** into the product repository,
  never a copy of its content;
- a blocker stays listed until a result supersedes it;
- `updated` is the date of the last real change, not of the last read.

---

# `log.md`

Append-only. Never edited, never reordered, never pruned.

One entry per orchestration event:

```markdown
## 2026-10-13 — envelope issued

worker: api-engineer
task: 941
envelope: envelopes/941-api-engineer.md
reason: Captain handoff repositories[1]

## 2026-10-13 — blocker received

worker: api-engineer
type: CONTRACT_CHANGE_REQUIRED
result: results/2026-10-13-api-engineer-941-blocker.md
routed_to: captain
```

`WORKFLOW-STATE.md` says where you are. `log.md` says how you got there.

When they disagree, `log.md` is the evidence and `WORKFLOW-STATE.md` is the
defect.

---

# `envelopes/`

One file per issued Task Envelope, containing the exact payload sent.

```text
envelopes/<ado-task>-<worker>.md
envelopes/941-api-engineer.md
```

A re-issued envelope after a resolved blocker appends a sequence suffix:

```text
envelopes/941-api-engineer-2.md
```

Never edit an issued envelope. An envelope is a record of what was actually
sent. Correcting it retroactively destroys the ability to explain a result.

---

# `results/`

One file per received Task Result or Blocker Result, containing the exact
payload returned.

```text
results/<date>-<worker>-<ado-task>.md
results/<date>-<worker>-<ado-task>-blocker.md
```

Received payloads are immutable. The `admiral` records them as returned,
including claims it intends to challenge.

If a claim is later disproved, that correction is a new `log.md` entry, not an
edit to the stored result.

---

# Persistence timing

Persist as events happen, not at the end of a session.

```text
envelope issued      -> write envelope file + log entry
result received      -> write result file + log entry + update WORKFLOW-STATE
blocker routed       -> log entry + update WORKFLOW-STATE
authorization given  -> update WORKFLOW-STATE
```

A session that persists only on completion loses everything when it is
interrupted. Interruption is the normal case in this environment, not the
exception.

---

# Resumption test

The layout satisfies its purpose when a new session, with no chat history, can
answer all of these from files alone:

1. What is this feature supposed to do? → `global-spec.md`
2. How was it decomposed and why? → `global-plan.md`, `contracts.md`
3. What was assigned, to whom? → `handoff.md`, `envelopes/`
4. What came back? → `results/`
5. Where are we now? → `WORKFLOW-STATE.md`
6. How did we get here? → `log.md`
7. What is actually implemented? → the product repository checkpoint it
   references

If any answer requires chat history, the state is incomplete.

---

# Version control

This repository is the durable layer. Durability requires version control.

Orchestration artifacts MUST be committed. An uncommitted
`WORKFLOW-STATE.md` in a container that can be recreated is not durable state.

Secrets are never written here. These files are committed and shared; the
security rules in the worker and orchestration agents apply to every artifact
in this repository.

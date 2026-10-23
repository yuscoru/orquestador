# Change and Issue Protocol

## Purpose

The feature workflow plans a feature once (`captain`, three gates) and executes it
(`admiral` + engineers). It says nothing about what happens **after** that
plan meets reality:

- an inconsistency, gap or wrong decision is found in the approved specification;
- an issue (defect, regression, unexpected behaviour) is found in what was built.

Without a path for these, the only options are to edit approved artifacts
silently or to ask an engineer to "just fix it" with no acceptance criteria, no
traceability and no record. Both are forbidden.

This protocol defines that path. It adds **two kinds of entry** and **one kind of
gate**. It does not change the planning gates 1 to 3 or the delivery gate 4.

```text
Finding  ->  Triage?  ->  FIX      (implementation defect)   no re-planning
                      ->  CHANGE   (specification changes)   delta gate, then re-implementation
                      ->  neither  (environment, data, or works as specified)
```

---

# Vocabulary

| Term | Meaning |
|---|---|
| **Issue** (`ISS-NNN`) | Something observed that is wrong or unexpected. Recorded before it is classified. |
| **Change Request** (`CR-NNN`) | A deliberate amendment of the approved spec, plan, tasks or contracts. |
| **FIX** | Envelope kind: correct an implementation that does not meet the approved spec. |
| **CHANGE** | Envelope kind: implement an approved Change Request. |
| **Delta gate** | Human approval of exactly what a Change Request amends, nothing more. |
| **Triage** | Classification of an issue, with repository evidence, into one outcome below. |

An issue is **not** a bug until triage says so. "The API returns 1 of 8
evaluations" was an issue; triage found it was working as specified, and the
next step was a Change Request, not a fix.

---

# Intake

Anyone may report a finding to the `admiral` or, for something that is clearly a
specification question, directly to the `captain`.

The `admiral` opens `issues/ISS-NNN.md` for every finding that may lead to code
work. A finding that is only a question needs no file.

Numbering is sequential per feature and never reused: `ISS-001`, `ISS-002`.

---

# When triage is required

Triage is **required only when the finding touches a contract or the
specification**. Otherwise the `admiral` may issue a FIX envelope directly.

A finding touches a contract or the specification if **any** of these holds:

1. the correction would change a request or response shape, status code,
   authorization rule, error contract or any entry of the feature's
   `contracts.md`;
2. the correction would change behaviour described by a functional requirement,
   acceptance criterion or success criterion of the global `spec.md`;
3. the cause is a decision recorded in `plan.md` or `contracts.md`;
4. the `admiral` cannot tell.

Rule 4 is deliberate: when in doubt, triage. Triage is cheap; a FIX that quietly
changes a contract is not.

A FIX that starts clean and then turns out to touch a contract or the spec stops
there: the engineer returns `SPEC_INCONSISTENCY` or `CONTRACT_CHANGE_REQUIRED`
and the finding goes to triage.

---

# Triage

Triage is **ungated**: it produces an answer, not an approved artifact, so the
`admiral` MAY invoke the `captain` as a subagent for it.

The `captain` asks the relevant analysts a `TRIAGE` question
(`worker-analysis.md`), one analyst at a time, and returns one outcome:

| Outcome | Meaning | Next |
|---|---|---|
| `IMPLEMENTATION_DEFECT` | The spec is right and the implementation does not meet it | FIX envelope; Bug in ADO |
| `SPEC_CHANGE` | The implementation matches the spec, and the spec is not what is wanted | Change Request |
| `SPEC_DEFECT` | The spec contradicts itself, a contract, or the plan | Change Request |
| `ENVIRONMENT_OR_DATA` | Cause is infrastructure, data or configuration, not product code | User or ops; no code |
| `NOT_A_DEFECT` | Works as specified and nobody wants it different | Close the issue with the evidence |

The triage answer MUST cite repository evidence and say what was verified versus
assumed. A conclusion that the API "cuadra" with the data store is evidence;
"it looks fine" is not.

The `admiral` records the outcome in `issues/ISS-NNN.md`.

---

# FIX

A FIX corrects the implementation **inside the approved spec**. It never
amends the spec and never changes a contract.

Envelope: `kind: FIX` (`task-envelope.md`). It MUST carry:

- the symptom, and the steps or evidence that reproduce it;
- the expected behaviour **as stated by the spec** (cite the requirement);
- a **regression test** written first, red before the fix and green after;
- the repository, and nothing wider.

The engineer records the fix in the repository's `IMPLEMENTATION-CHECKPOINT.md`
(what was wrong, what changed, the regression test) and never edits `plan.md`.

FIX work is tracked by its ADO Bug, not by a spec task. `spec_tasks` is empty.

The branch is the feature branch while that feature is unmerged. If it has
already been merged, the `admiral` stops and asks the user which branch to use;
this protocol does not invent a naming scheme.

---

# Change Request

A Change Request amends approved planning artifacts. It is **planning work** and
therefore gated and user-driven; it cannot run inside a subagent.

Owner: `captain`. File: `specs/<ADO-US>-<slug>/changes/CR-NNN.md`.

## Sequence

```text
CR requested
     |
     v
captain drafts CR-NNN.md           status: DRAFT
     |  amends spec / plan / tasks / contracts IN PLACE (see below)
     |  runs /speckit.analyze on the amended artifacts
     v
DELTA GATE                          user approves the delta, only the delta
     |
     v
status: APPROVED                    CR file and amended artifacts record the gate
     |
     v
captain creates ADO Tasks           child of the US, tagged with the CR id
     |
     v
admiral issues CHANGE envelopes     one per repository, one at a time
     |
     v
status: APPLIED  ->  CLOSED         when results are verified
```

An unapproved CR is a draft. The `admiral` MUST NOT issue CHANGE envelopes from
a draft.

## Amend in place; never regenerate

The `captain` edits the existing artifacts. It MUST NOT re-run
`/speckit.specify`, `/speckit.plan` or `/speckit.tasks` over an approved
feature: they regenerate the whole artifact, renumber tasks and discard history.

Spec Kit commands that are allowed:

- `/speckit.analyze`, mandatory before the delta gate, to check the amended
  artifacts are consistent with each other;
- `/speckit.clarify`, to resolve an open question the CR raises.

## Where the change lives

| Artifact | How the CR is reflected |
|---|---|
| `changes/CR-NNN.md` | The record: motive, delta, impact, task delta, gate, ADO links |
| `spec.md` | The affected requirement is edited in place, marked `(amended by CR-NNN)`. A section `## Amendments` lists what each CR changed, with the previous wording |
| `plan.md` | The affected section is edited in place and marked the same way |
| `tasks.md` | **Existing ids are never renumbered or deleted.** New tasks take the next free ids, tagged `[CR-NNN]`. A superseded task keeps its line and gains `superseded by T0xx (CR-NNN)`. A task already `[x]` stays `[x]`: the work was done |
| `contracts.md` | The affected contract is updated. Contract change propagation applies as always |
| `handoff.md` | Not rewritten. The CR carries its own `execution_order` |

Task ids stay the thread between the global `tasks.md`, the envelope's
`spec_tasks`, the repository's `tasks.md` and the commit trailer.

## The delta gate

One approval covers the whole CR, but only what the CR changes. The `captain`
presents the exact delta: requirements before and after, the contracts touched,
tasks superseded and added, repositories affected, and what is most likely to be
wrong. It does not re-present the unchanged feature.

Approval is an explicit affirmative. It is recorded in `CR-NNN.md` and next to
each amendment:

```markdown
> Gate: delta approved by user on 2026-10-16 (CR-001).
```

A question, silence or a partial edit request is not approval. On rejection,
record why in the CR, revise, and return to the same gate.

## Effect on a running feature

While a CR is `DRAFT` or awaiting its gate, the `admiral` does not issue new
FEATURE envelopes for tasks that CR would supersede. Work in repositories the CR
does not touch may continue. The `admiral` records the CR under `open_changes`
in `WORKFLOW-STATE.md` and the feature phase becomes `CHANGE_PENDING`.

After approval, repositories that already implemented a superseded task receive
a CHANGE envelope. They re-project only the delta into their local
`spec.md`, `plan.md` and `tasks.md`, preserving finished work and original ids.

---

# Azure DevOps

ADO work items are written only by an agent holding `update_ado` authorization
for the feature. An item is never reported as created unless it was read back.

## Who creates what

| ADO item | Created by | When |
|---|---|---|
| **Bug** | `admiral` | Outcome `IMPLEMENTATION_DEFECT`, or a direct FIX that skipped triage |
| **Task** for a CR | `captain` | After the delta gate, one per affected repository |
| Comment on the User Story | `captain` | When the CR is approved; and when it closes |
| Updates on an assigned Bug or Task | the engineer | Under its envelope, as today |

Engineers never create work items. An engineer that finds a defect returns a
Result or Blocker; the `admiral` opens the Bug.

Outcomes `SPEC_CHANGE` and `SPEC_DEFECT` create no Bug: the work item is the CR's
Task. `NOT_A_DEFECT` and `ENVIRONMENT_OR_DATA` create none unless the user asks.

## Shape

**Bug**

- type Bug, title `[ISS-NNN] <symptom>`, tag `iss-nnn`;
- parent: the User Story;
- related to the Task whose delivery exposed it, when there is one;
- reproduction steps and expected versus actual, with no credentials, tokens or
  user data;
- stays `Active` until the repository's merge policy allows closure, like Tasks.

**Change Request**

- no new User Story. The CR amends the feature the User Story already owns;
- one **Task** per affected repository, child of the User Story, title
  `[CR-NNN] <what changes in this repository>`, tag `cr-nnn`;
- a comment on the User Story with the CR summary, the delta and the gate date;
- existing Tasks are left as they are. A superseded Task gets a comment linking
  to the CR; it is not closed or reopened by this protocol;
- a change large enough to be a different capability is a **new User Story**
  related to the original. That decision belongs to the user.

The ids of everything created are written into `CR-NNN.md` or `ISS-NNN.md`.

## Commit trailer

```text
Refs: #<US> #<taskId>          CHANGE: the CR Task
Refs: #<US> #<bugId>           FIX: the Bug
```

---

# Artifacts

## `issues/ISS-NNN.md` (owner: `admiral`)

```markdown
# ISS-001 — <symptom>

status: OPEN | TRIAGED | FIX_ISSUED | RESOLVED | CLOSED_NOT_A_DEFECT | SUPERSEDED_BY_CR
reported: <date> by <who>
repository: <repo or "unknown">
touches_contract_or_spec: yes | no | unsure
triage: required | skipped

## Observation
What was seen and how to reproduce it. No secrets.

## Triage
outcome: IMPLEMENTATION_DEFECT | SPEC_CHANGE | SPEC_DEFECT | ENVIRONMENT_OR_DATA | NOT_A_DEFECT
evidence: <path / query / output, verified versus assumed>

## Routing
FIX envelope | CR-NNN | none, and why

## ADO
bug: #<id> (confirmed by read-back) | none, and why
```

## `changes/CR-NNN.md` (owner: `captain`)

```markdown
# CR-001 — <title>

status: DRAFT | APPROVED | APPLIED | CLOSED | REJECTED
origin: ISS-NNN | direct
requested: <date> by <who>

## Motive
## Delta
Requirement by requirement: previous wording, new wording.
## Impact
Per repository: affected or not, and why.
## Contracts affected
## Task delta
superseded: [T012, ...]    new: [T027, ...]
## Execution order
## Gate
> Gate: delta approved by user on <date> (CR-001).
## ADO
tasks: #<id> ...   user story comment: <id>   (confirmed by read-back)
## History
```

---

# Blockers

`SPEC_INCONSISTENCY` (`blocker-result.md`) is returned by an engineer or analyst
that finds the specification contradicts itself, a contract or the code. It is
routed to the `captain`, who opens or amends a Change Request.

`CONTRACT_CHANGE_REQUIRED`, `REQUIREMENT_AMBIGUITY` and `SCOPE_EXPANSION_REQUIRED`
keep their meaning and may also end in a Change Request.

---

# State

`WORKFLOW-STATE.md` gains:

```yaml
open_changes:
  - id: CR-001
    status: DRAFT          # DRAFT | APPROVED | APPLIED
    file: changes/CR-001.md
open_issues:
  - id: ISS-001
    status: TRIAGED
    file: issues/ISS-001.md
```

and two phases, defined in the `admiral` state model:

```text
CHANGE_PENDING   a CR is drafted or awaiting its delta gate
REOPENED         a FIX or an approved CR returned the feature to implementation
```

`IMPLEMENTATION_COMPLETE` is therefore not final: it may be left again, through
`REOPENED`, and every such transition has a file that explains it.

---

# Invariants

1. A finding is recorded before it is classified.
2. Triage is required only when a contract or the spec is touched, and is
   always required when that is unclear.
3. A FIX never amends the spec or a contract.
4. A Change Request amends artifacts in place; it never regenerates them.
5. Task ids are never renumbered; superseded work stays visible.
6. A Change Request needs the delta gate; one gate, covering the delta only.
7. The delta gate is user-driven and never delegated to a subagent.
8. Engineers never create ADO work items.
9. A Bug exists only for a confirmed implementation defect.
10. A work item or comment counts as created only after it is read back.

# Feature Branching Protocol

## Purpose

Spec Kit numbers feature branches sequentially (`001-slug`, `002-slug`). SOAR+
features are identified by their Azure DevOps User Story id and span several
repositories.

Left to its defaults, Spec Kit would generate a different number in every
repository for the same feature, and traceability to the User Story would be
lost.

This protocol fixes the mechanism that prevents it.

It applies to **every repository with Spec Kit installed**:

```text
soarplus-dev-orchestration
soarplus-agentics
soarplus-api
soarplus-frontend-app1
```

and to any repository that installs it later.

---

# Canonical identity

The Azure DevOps User Story id is the feature id.

```text
branch        feature/<ADO-US>-<slug>
spec dir      specs/<ADO-US>-<slug>/
commit refs   Refs: #<ADO-US> #<taskId>
```

Example:

```text
feature/696-sre-response-quality
specs/696-sre-response-quality/
```

**The same branch name is used in every repository** touched by the feature. It
is the only thing that correlates the work across repositories.

The slug is chosen once, by the `captain`, when the global specification is
created. Every repository reuses it verbatim. A repository MUST NOT re-derive
its own slug from the feature description.

---

# The mechanism

`speckit.git.feature` runs `create-new-feature.sh`, which honours an environment
override:

```bash
export GIT_BRANCH_NAME="feature/696-sre-response-quality"
```

When set, the script uses that exact name and **bypasses all prefix and
numbering generation**.

This MUST be exported before any command that creates a branch.

## Why it must be exported first

`.specify/extensions.yml` registers:

```yaml
before_specify:
  - extension: git
    command: speckit.git.feature
    optional: false
```

with `auto_execute_hooks: true`.

`/speckit.specify` therefore creates a branch **automatically**, before asking
anything. If `GIT_BRANCH_NAME` is not already set, the branch is numbered
sequentially and the convention is broken from the first command.

Recovering requires renaming the branch and relinking the ADO artifact. This has
already happened once in `soarplus-agentics`, where
`feature/SRE_response_quality` had to be renamed to
`feature/696-sre-response-quality`.

## What the configuration does not do

`.specify/extensions/git/git-config.yml` has no `branch_prefix` setting. The
`feature/` prefix is **not** configurable and is not produced by Spec Kit.

It exists only because this protocol imposes it through `GIT_BRANCH_NAME`.

Do not look for a configuration file that enforces this. There is none. The
export is the enforcement.

---

# Who creates which branch

| Repository | Branch created by | When |
|---|---|---|
| `soarplus-dev-orchestration` | `captain` | before `/speckit.specify` for the global spec |
| product repository | its `-engineer` | on receiving the first Task Envelope for the feature |

An `-analyst` never creates or switches a branch.

The `admiral` never creates a branch in a product repository; it states the
expected branch in `repository.branch` of the Task Envelope.

---

# Engineer obligations

On receiving a Task Envelope, before any write:

1. Read `repository.branch` from the envelope.
2. If already on that branch, continue.
3. If the branch exists locally, switch to it.
4. If it does not exist, create it with the exact name from the envelope.

```bash
export GIT_BRANCH_NAME="<repository.branch>"
```

Never infer the branch name. Never let Spec Kit generate it.

If the active branch differs from `repository.branch` and the difference cannot
be resolved safely, stop and return:

```text
BLOCKED / BRANCH_MISMATCH
```

If the envelope's branch does not follow `feature/<ADO-US>-<slug>`, that is an
orchestration defect. Return the blocker rather than normalizing it silently.

---

# Spec directory binding

Spec Kit resolves the active feature directory through `SPECIFY_FEATURE` or
`.specify/feature.json`.

After creating or switching to the feature branch, confirm the active feature
directory is:

```text
specs/<ADO-US>-<slug>/
```

A branch and a spec directory that identify different features is a
`FEATURE_MISMATCH`, not something to repair by guessing which one is right.

---

# Azure DevOps linking

A User Story accepts multiple branch `ArtifactLink` relations, one per
repository.

Each repository's feature branch SHOULD be linked to the User Story so the work
is traceable from the work item.

Creating the branch and linking it are distinct operations. Do not report the
link as done unless it was confirmed.

---

# Prohibited

- Letting Spec Kit assign a sequential number to a SOAR+ feature branch.
- Using a different slug in different repositories for the same User Story.
- Creating a feature branch in a repository that has no work in the feature.
  Branches are created when real work starts, not in advance.
- Renaming a branch after artifacts reference it, without updating those
  references and the ADO link.
- Inventing a User Story id to satisfy the naming convention. If there is no
  User Story, there is no feature branch yet.

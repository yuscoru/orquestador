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

Two **independent** environment variables control two independent things. Both
are required. Setting only one produces a branch and a directory that disagree.

```bash
export GIT_BRANCH_NAME="feature/696-sre-response-quality"
export SPECIFY_FEATURE_DIRECTORY="specs/696-sre-response-quality"
```

| Variable | Controls | Read by |
|---|---|---|
| `GIT_BRANCH_NAME` | the branch name | `speckit.git.feature` extension script |
| `SPECIFY_FEATURE_DIRECTORY` | the spec directory | `/speckit.specify`, and `get_feature_paths` for plan/tasks/implement |

The branch keeps the `feature/` prefix. The directory does not. They are
deliberately different strings, which is why one variable cannot serve both.

Verified behaviour, dry-run, no side effects:

```text
no variables        -> branch 001-sre-response-quality
GIT_BRANCH_NAME set -> branch feature/696-sre-response-quality
```

`/speckit.specify` persists the resolved directory into
`.specify/feature.json`, so later commands in that repository resolve it
without the variable being re-exported.

## Why both are needed

`GIT_BRANCH_NAME` bypasses numbering but the extension then reports
`FEATURE_NUM` as the **whole branch string**, because the extraction regex
expects a leading digit and `feature/696-...` starts with a letter.

Any code path that derives a directory from that value would produce the nested
`specs/feature/696-sre-response-quality/`.

`SPECIFY_FEATURE_DIRECTORY` removes the dependency entirely: the directory is
stated, not derived.

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

Do not look for a configuration file that enforces this. There is none. The two
exports are the enforcement.

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
2. Export both variables:

```bash
export GIT_BRANCH_NAME="<repository.branch>"
export SPECIFY_FEATURE_DIRECTORY="specs/<ADO-US>-<slug>"
```

3. If already on that branch, continue.
4. If the branch exists locally, switch to it.
5. If it does not exist, create it with the exact name from the envelope.

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

Spec Kit resolves the active feature directory in this priority order:

```text
1. SPECIFY_FEATURE_DIRECTORY   explicit override
2. .specify/feature.json       persisted by /speckit.specify
3. branch-name prefix lookup   legacy fallback
```

The branch-name fallback is the one that would break the convention. Keep
resolution at level 1 or 2.

The active feature directory MUST be:

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

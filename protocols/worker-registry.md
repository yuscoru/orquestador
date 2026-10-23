# Worker Registry Protocol

## Purpose

This registry is the **single source of truth** mapping a logical worker
identifier to the agent that implements it and the repository it owns.

Every protocol that names a worker — `task-envelope.md`, `worker-analysis.md`,
`task-result.md`, `blocker-result.md` — resolves that name here.

No other document may define, extend or alias worker identifiers.

---

# Identity rule

For every worker, these four strings are **identical**:

```text
the protocol `worker:` value
the agent `name` in frontmatter
the agent filename stem under .github/agents/
the invocation handle used to call it as a subagent
```

Example:

```text
worker: api-engineer
.github/agents/api-engineer.agent.md
name: api-engineer
```

This removes any translation step between orchestration and invocation.

A caller MUST NOT invent a display variant such as `API Engineer`,
`api_engineer` or `apiEngineer`.

Identifiers are lowercase kebab-case: `<repository-role>`.

---

# Registered workers

| worker | repository | mode | agent file |
|---|---|---|---|
| `agentics-analyst` | `soarplus-agentics` | `ANALYZE` | `.github/agents/agentics-analyst.agent.md` |
| `agentics-engineer` | `soarplus-agentics` | `IMPLEMENT` | `.github/agents/agentics-engineer.agent.md` |
| `api-analyst` | `soarplus-api` | `ANALYZE` | `.github/agents/api-analyst.agent.md` |
| `api-engineer` | `soarplus-api` | `IMPLEMENT` | `.github/agents/api-engineer.agent.md` |
| `frontend-analyst` | `soarplus-frontend-app1` | `ANALYZE` | `.github/agents/frontend-analyst.agent.md` |
| `frontend-engineer` | `soarplus-frontend-app1` | `IMPLEMENT` | `.github/agents/frontend-engineer.agent.md` |

Repository paths in this environment:

```text
soarplus-agentics      -> /root/soarplus-agentics
soarplus-api           -> /root/soarplus-api
soarplus-frontend-app1 -> /root/soarplus-frontend-app1
```

---

# Mode pairing

Each repository exposes exactly two workers, split by mode.

```text
<repository>-analyst    ANALYZE    read-only, never modifies state
<repository>-engineer   IMPLEMENT  writes only inside its owned repository
```

Routing rules:

- a `worker-analysis.md` request MUST target an `-analyst`;
- a `task-envelope.md` assignment MUST target an `-engineer`;
- a worker MUST reject a request whose mode does not match its registered mode;
- a worker MUST reject an assignment for a repository it does not own.

An `-analyst` never receives a Task Envelope. An `-engineer` never receives an
analysis request.

---

# Invocation visibility

The routing hierarchy is enforced in each agent's YAML frontmatter, not only in
prose:

| agent | `user-invocable` | `disable-model-invocation` | `agents` |
|---|---|---|---|
| `admiral` | default (`true`) | `true` | `[captain, *-engineer]` |
| `captain` | default (`true`) | default (`false`) | `[*-analyst]` |
| `*-analyst` | `false` | default (`false`) | `[]` |
| `*-engineer` | `false` | default (`false`) | `[]` |

Consequences:

- only `admiral` and `captain` appear in the agent picker; a human enters the
  system through one of them;
- workers are reachable only as subagents, which matches the protocols — an
  `-analyst` needs a `worker-analysis.md` request and an `-engineer` needs a
  Task Envelope, and neither exists in a free-form user prompt;
- `agents: []` prevents a worker from sub-delegating, so repository write
  ownership cannot be laundered through a second worker;
- `admiral` is not model-invocable, so no agent can route work back into the
  orchestrator. The `captain` reaches it through a handoff, which the user
  confirms.

Changing any of these fields changes the shared agent definition for everyone
who clones the repository. Update this table in the same change.

---

# Pi team

A separate set of workers for the Pi team (`pi/team.md`). Each owns one repository and serves
both modes, `ANALYZE` and `IMPLEMENT`; the mode travels in each request, not in the worker.
They do not use the `-analyst` / `-engineer` identifiers above, and `pi/launch.sh` and
`pi/team.sh` read this table to resolve repositories.

| worker | repository | modes |
|---|---|---|
| `agentics` | `soarplus-agentics` | ANALYZE, IMPLEMENT |
| `api` | `soarplus-api` | ANALYZE, IMPLEMENT |
| `frontend` | `soarplus-frontend-app1` | ANALYZE, IMPLEMENT |

The link name of every Pi role, including `admiral`, is `<role>@soarplus`. The Pi team has no
`captain`: planning is a phase of the `admiral`.

---

# Not yet registered

The following identifiers appear in orchestration discussion but have **no**
implementing agent. They MUST NOT be used as a `worker:` value.

```text
runner-analyst   / runner-engineer      soarplus-runner
k8s-analyst      / k8s-engineer         soarplus-kubernetes
```

They MAY appear as a blocker `owner` to express that work belongs to an
unimplemented worker. In that case the Admiral routes the work to a human.

Adding a worker means adding both the agent file and a row above, in the same
change.

---

# Non-worker roles

These are orchestration roles, not repository workers. They own routing and
architecture, never repository-local implementation.

| role | owns | agent file |
|---|---|---|
| `admiral` | workflow routing, Task Envelope issuance | `.github/agents/admiral.agent.md` |
| `captain` | global architecture, cross-repository analysis | `.github/agents/captain.agent.md` |

A non-worker role is never a valid `worker:` value and never receives a Task
Envelope or returns a Task Result. It MAY be a blocker `owner`.

The `admiral` is the only role that issues Task Envelopes. It delegates to the
`captain` and to `-engineer` workers, and never calls an `-analyst` directly.

The `captain` writes only to `soarplus-dev-orchestration` and delegates
repository investigation to the registered `-analyst` workers. It MUST NOT
invoke `-engineer` workers.

Additional non-worker blocker owners:

```text
reviewer
user
external
```

---

# Repositories without a worker

```text
soarplus-dev-orchestration   protocol host, no repository worker
soarplus-development-agents  no registered worker
```

Work in a repository with no registered worker is not assignable. Return a
blocker and let the Admiral route it.

---

# Validation

Before accepting any request, a worker MUST confirm:

1. the `worker` value in the request equals its own registered identifier;
2. the `repository.name` equals the repository registered for that identifier;
3. the request mode equals its registered mode.

Any mismatch is a blocker, not something to reconcile silently.

Expected blocker classifications:

```text
BLOCKED / WORKER_MISMATCH        worker absent, unregistered, or not you
BLOCKED / REPOSITORY_MISMATCH    repository does not match the registry
```

A worker MUST NOT accept a request addressed to a different worker, even when
it is technically capable of performing the work.

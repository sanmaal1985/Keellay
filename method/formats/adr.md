# ADR

An architecture decision record keeps one decision that constrains future work, with the options that were weighed
and why the others lost. ADRs are append-only: a decision is changed by a new ADR that supersedes the old one, never
by editing it. The index says which decisions are in force now.

**What gets an ADR:** decisions that will still matter after the current change closes: architecture, process,
tooling, conventions, and tools or approaches that were evaluated and declined. A choice that only matters inside one
change stays in that change's Decisions section.

## File

`docs/adr/<number>-<topic>.md`, where the number is `A` and at least four digits (`A0012`), sequential and never
reused (see [Numbers](README.md)).

```markdown
---
id: A0012
title: Sessions expire after inactivity, not after a fixed time
status: accepted         # proposed | accepted | superseded
date: 2026-11-20
decided-by: owner
supersedes: A0004        # optional; a list when it replaces several: [A0004, A0007]
superseded-by:           # set only when a later ADR replaces this one
---

# A0012 Sessions expire after inactivity, not after a fixed time

## Context

What forced a decision: the problem, the constraints, what is known. Links to the change, research or idea.

## Options

- **Inactivity timeout** — ...
- **Fixed 24-hour lifetime** (current) — ...
- **Refresh tokens** — ...

## Decision

The option chosen, in one or two sentences, stated as a rule someone can follow.

## Consequences

What becomes easier, what becomes harder, what has to be done because of it.
```

## Rules

- **Frozen once accepted.** After `accepted`, only `status` and `superseded-by` may change.
- **Changing a decision** is a new ADR with `supersedes`. It restates the whole rule as it is now, including what it
  keeps from the old one, so the reader never has to combine two ADRs. The old ADR gets `status: superseded` and
  `superseded-by` in the same commit. When a new decision changes several ADRs at once, one ADR may supersede all of
  them (`supersedes` as a list); each old one names it in `superseded-by`.
- **Declined options count.** "We evaluated X and do not use it" is a decision worth an ADR, so the question is not
  reopened from scratch.

## Index: docs/adr/README.md

Lists only what is in force, then what was replaced:

```markdown
# Decisions

In force:

| ADR | Decision |
|---|---|
| [A0012](A0012-session-inactivity-timeout.md) | Sessions expire after inactivity, not after a fixed time |

Replaced:

| ADR | Replaced by |
|---|---|
| [A0004](A0004-session-lifetime.md) | A0012 |
```

## Checked by

`keellay check`: front matter; numbers unique; the index lists exactly the accepted ADRs under "In force" and the
superseded ones under "Replaced". Planned: an accepted ADR's body is unchanged since acceptance (compared with git
history; light: advice, standard: warning, strict: error); `supersedes` and `superseded-by` agree.

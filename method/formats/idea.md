# Idea

An idea is a proposal not yet approved as work: from the owner, a user, an agent or a retro. It is written down as
proposed, assessed against the PRD and the decisions in force, and then either planned as a change or declined with
the reason, so the same idea is not argued again from scratch.

## File

`docs/product/ideas/<number>-<topic>.md`, with a four-digit sequential number that is never reused.

```markdown
---
id: 0004
title: Shared limits for two households
status: assessed         # new | assessed | planned | done | declined
verdict: clarify         # go | clarify | stop; set when assessed
source: owner            # owner | user | agent | retro
date: 2026-11-21
prd: PRD-limits          # optional: the PRD area it serves
change:                  # the change that carries it, set when that change is approved
---

# 0004 Shared limits for two households

## Proposal

What is proposed and why, in the proposer's words. Who asked and in what context.

## Assessment

- Value: which PRD outcome it serves, or why it is worth a new area.
- Cost and risk: rough size, areas touched, what could break.
- Fit: conflicts with Non-goals, ADRs in force or open changes.
- Verdict: go, clarify or stop, with the reason. For clarify, the questions for the owner.

## Outcome

The owner's decision: planned (and later the change link), or declined with the reason.
```

## Lifecycle

`new` → `assessed` → `planned` → `done`, or `declined` from any state before `done`.

| Status | Meaning | Who moves it here |
|---|---|---|
| new | written down as proposed, not assessed | anyone |
| assessed | Assessment filled in, `verdict` set | product owner |
| planned | the owner said yes; `change` is set when the change that carries it is approved | owner |
| done | the change that carries it closed | architect, at the change's close |
| declined | will not be done; the reason is in Outcome | owner |

- **The verdict advises, the owner decides.** A `go` verdict does not plan an idea and a `stop` verdict does not decline
  it; only the owner moves an idea to `planned` or `declined`.
- **Clarify** keeps the idea `assessed` until the owner answers; the answers go into Assessment and the verdict is set
  again.
- **Declined ideas stay.** They are the record of what was considered and why not.
- **A dropped change** leaves its ideas `planned` without a change, or `declined`, as the owner says; the product
  owner records it and clears `change`.
- An idea that will be done straight away may go from `new` to `planned` when the owner says so; `verdict` stays empty
  and Assessment holds one line on why it was skipped.

## Index: docs/product/README.md

The product index links to the PRD and holds the ideas register: open ideas in the owner's order of priority, then
the closed ones.

```markdown
# Product

- [PRD](prd.md)

Ideas, open (in order of priority):

| Idea | Title | Status | Verdict | Change |
|---|---|---|---|---|
| [0004](ideas/0004-shared-limits.md) | Shared limits for two households | assessed | clarify | |
| [0002](ideas/0002-receipt-photo.md) | Receipt photo on an entry | planned | go | 0009 |

Ideas, closed:

| Idea | Title | Status |
|---|---|---|
| [0001](ideas/0001-bank-import.md) | Import from the bank | declined |
```

## Checked by

`keellay check`: front matter fields and values. Planned: numbers unique; `assessed` has a `verdict`, and a later
status keeps it unless Assessment says why it was skipped; `declined` has an Outcome; `change` names an existing
change, and `done` names a closed one; `prd` names an existing PRD area; the index lists every idea once, in the table
that matches its status.

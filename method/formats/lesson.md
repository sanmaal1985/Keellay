# Lesson

A lesson records something that went wrong (or nearly did), why the process let it through, and what stops it next
time. Lessons exist to become mechanisms: a lesson that repeats gets a hook, a check, a contract rule or a checklist
item, and then stops costing attention.

## File

`docs/lessons/<number>-<topic>.md`, with a four-digit sequential number that is never reused.

```markdown
---
id: 0003
title: Conventions were chosen without the owner
status: active           # active | mechanized | retired
count: 2                 # times it happened
first: 2026-11-20
last: 2026-11-21
mechanism:               # what enforces it once mechanized: a hook, check, contract rule or checklist item
---

# 0003 Conventions were chosen without the owner

## Occurrences

- 2026-11-20, change 0011: the agent wrote a branch-name convention into the agent instructions without asking.
- 2026-11-21, change 0003: ...

## Gap

Which mechanism should have caught it and why it did not: there was none, it was too weak, or it did not cover this
case.

## Rule

What to do instead, in one sentence an agent can follow.

## Mechanism

What will enforce the rule, or what does already. Empty while there is none.
```

## Lifecycle

- **active:** the rule is in force and agents read it; `count` grows with each repeat.
- **Repeats force a mechanism:** when `count` reaches 2, the lesson must get a mechanism before the change in which it
  repeated closes, unless the owner waives it in that change's Decisions.
- **mechanized:** the mechanism is in place and named in `mechanism`; agents no longer need to read the lesson.
- **retired:** no longer relevant, with the reason in the file.

**Where lessons come from:** the retro after a change closes (level standard and up), and any moment the owner or an
agent sees the process fail. The change's Close section links the lessons it created or updated.

## Index: docs/lessons/README.md

Active lessons are what agents read; the rest is history.

```markdown
# Lessons

Active (read before working):

| Lesson | Rule | Count |
|---|---|---|
| [0003](0003-conventions-without-owner.md) | Conventions and other choices go to the owner as options with a recommendation | 2 |

Mechanized:

| Lesson | Mechanism |
|---|---|
| [0001](0001-attribution-in-public-commits.md) | `commit-msg` hook |
```

## Checked by

`keellay check` (task 4): front matter; numbers unique; `count` equals the number of occurrences; a lesson with
`count` of 2 or more is mechanized, or has an owner waiver, before its change closes; `mechanized` has a `mechanism`;
the index lists active and mechanized lessons in the right tables.

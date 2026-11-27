# Lesson

A lesson records something that went wrong (or nearly did), why the process let it through, and what stops it next
time. Lessons exist to become mechanisms: a lesson that repeats gets a hook, a check, a rule in a role skill, a
checklist item or, weakest, a rule in the constitution or the agent instructions, and then stops costing attention.

## File

`docs/lessons/<number>-<topic>.md`, where the number is `L` and at least four digits (`L0003`), sequential and
never reused (see Numbers in the formats' README).

```markdown
---
id: L0003
title: A migration ran without a backup
status: active           # active | mechanized | retired
count: 2                 # times it happened
first: 2026-03-02
last: 2026-04-15
mechanism:               # what enforces it once mechanized: a hook, check, role skill rule, checklist item or rule
---

# L0003 A migration ran without a backup

## Occurrences

- 2026-03-02, C0011: a schema migration ran on the staging database before its backup finished.
- 2026-04-15, C0019: ...

## Gap

Which mechanism should have caught it and why it did not: there was none, it was too weak, or it did not cover this
case.

## Rule

What to do instead, in one sentence an agent can follow.

## Mechanism

What will enforce the rule, or what does already. Empty while there is none.
```

A front matter field set later (`mechanism`) may be left out until it has a value.

## Lifecycle

- **active:** the rule is in force and agents read it; `count` grows with each repeat.
- **Repeats force a mechanism:** when `count` reaches 2, the lesson must get a mechanism before the change in which it
  repeated closes. A small mechanism (a rule in a role skill's project section, a checklist item, a constitution rule)
  is made at review with the owner's yes and re-reviewed in a fresh context. A large one (a hook, a check) is planned
  as a change of its own, and one that needs the method itself changed (a contract, a format) becomes an idea for
  Keellay; for either the owner waives the mechanism for this change in its Decisions.
- **mechanized:** the mechanism is in place and named in `mechanism`; agents no longer need to read the lesson.
- **retired:** no longer relevant, with the reason in the file.

**Where lessons come from:** the retro at review, before a change closes (level standard and up), and any moment the
owner or an agent sees the process fail. The change's Close section links the lessons it created or updated.

## Index: docs/lessons/README.md

Active lessons are what agents read; the rest is history.

```markdown
# Lessons

Active (read before working):

| Lesson | Rule | Count |
|---|---|---|
| [L0003](L0003-migration-without-backup.md) | A migration runs only after its backup is verified | 2 |

Mechanized:

| Lesson | Mechanism |
|---|---|
| [L0001](L0001-secrets-in-logs.md) | log redaction check in CI |
```

## Checked by

`keellay check`: front matter; numbers unique; the index lists active and mechanized lessons in the right tables;
`count` equals the number of occurrences; `mechanized` has a `mechanism`; a lesson still `active` with `count` of 2 or
more whose last occurrence names a closed change has the owner's waiver in that change's Decisions, which name the
lesson by its ID.

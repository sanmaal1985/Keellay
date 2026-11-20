# Change

A change is one unit of work that the owner approved: a folder with a plan and, when behaviour changes, spec deltas.
The fix path has no change folder (see [bugfix.md](bugfix.md)).

## Identity

- **ID:** `<number>-<topic>`, e.g. `0007-session-expiry`. The number has four digits, is sequential per project and is
  never reused; the topic is lowercase words joined by hyphens.
- **Claiming a number:** the row in the changes index claims it. When two branches claim the same number, the check
  fails on the second one and it takes the next free number.
- **Branch:** `<type>/<id>`, e.g. `feat/0007-session-expiry`. Types follow commit messages: `feat`, `fix`, `docs`,
  `ci`, `chore`, `refactor`, `test`. Work without a change uses `<type>/<topic>`.
- The pattern is configurable in `.keellay/config.toml`, so a project that keys work by tracker IDs (e.g.
  `feat/PROJ-123-session-expiry`) keeps them.

## Folder

```
docs/changes/
  README.md                 index of open changes
  0007-session-expiry/
    plan.md                 required
    design.md               optional: options considered for a feature; lasting decisions become ADRs
    delta/
      auth-session.md       one file per capability whose behaviour changes (see delta.md)
  archive/
    0006-.../               closed and dropped changes, moved here unchanged
```

## Lifecycle

`draft` → `approved` → `in-progress` → `review` → `closed`, or `dropped` from any state before `closed`.

| Status | Meaning | Who moves it here |
|---|---|---|
| draft | intent and scope written, not yet agreed | anyone |
| approved | the owner said yes to intent, scope and path | owner |
| in-progress | phases are being worked on | the role of the first phase |
| review | all phases done; a fresh-context review runs, deltas are merged into living specs | architect |
| closed | review passed, deltas merged, the folder moved to `archive/` | architect, with the owner's yes |
| dropped | will not be done; the reason is in the plan; moved to `archive/` | owner |

Every status change updates the index in the same commit.

## plan.md

```markdown
---
id: 0007-session-expiry
title: Session expires after inactivity
path: feature            # change | feature
status: in-progress
approved: 2026-11-20     # date of the owner's yes
---

# 0007 Session expires after inactivity

## Intent

Why this change exists and what is true when it is done. Links to the idea or PRD section it serves.

## Scope

- In: ...
- Out: ...

## Phases

### 1. Expiry rule in the session service

- Role: developer
- Depends on: —
- Done when: inactive sessions end after the configured timeout; scenarios in `delta/auth-session.md` pass as tests.

- [ ] step
- [ ] step

### 2. Expired-session screen

- Role: developer-flutter
- Depends on: 1
- Done when: ...

## Decisions

Decisions made during the change. One that will matter after the change closes becomes an ADR; link it here.

## Close

- Review: fresh-context session, date, result and findings.
- Merged deltas: `auth-session` (+REQ-auth-004, ~REQ-auth-003).
- ADRs: links. Lessons: links.
```

- **Role** names come from the project's roles: a core role or an instance of one. It is a closed list; a phase with
  an unknown role fails the check.
- **Depends on** lists phase numbers. Phases whose dependencies are done form a wave and can run in parallel.
- **Done when** is a condition someone else can verify, not a list of activities.
- A `change`-path plan may have one phase and no Decisions section.

## Index: docs/changes/README.md

```markdown
# Changes

Open changes. Closed and dropped ones are in `archive/`.

| ID | Title | Path | Status |
|---|---|---|---|
| [0007](0007-session-expiry/plan.md) | Session expires after inactivity | feature | in-progress |
```

## Checked by

`keellay check` (task 4): front matter fields and values; status matches the index row; one index row per open
change; no duplicate numbers; every phase has Role, Depends on and Done when; roles are known; the branch name
matches an open change (level light: advice, standard: warning, strict: error).

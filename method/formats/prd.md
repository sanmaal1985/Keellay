# PRD

The product requirements document says what the product is for, who it serves and which outcomes it commits to. It
is the "why" above the living specs: a spec says what the system does, the PRD says what the product should achieve
and where its boundary is. Changes and ideas link to its sections.

## File

`docs/product/prd.md`, one per project.

```markdown
---
product: Family budget
updated: 2026-11-21
---

# Family budget

## Purpose

The problem the product solves and for whom, in a few sentences.

## Users

- **Household member** — records spending from a phone, usually right after paying.
- **Budget keeper** — sets limits and reviews the month.

## Non-goals

- Investment tracking.
- Bank synchronisation in the first year.

## Areas

### PRD-capture: Spending is recorded at the moment of payment

- Outcome: a household member records a purchase in under ten seconds, offline included.
- Measure: median time from opening the app to a saved entry.
- In: manual entry, receipt photo. Out: bank import.
- Status: delivered

### PRD-limits: The keeper sees a limit coming before it is crossed

- Outcome: ...
- Measure: ...
- In: ... Out: ...
- Status: planned
```

## Areas

An area is one outcome the product commits to; it is the unit that changes and ideas link to.

- **ID:** `PRD-<topic>`, lowercase words joined by hyphens, unique in the file and never reused, also after the area is
  removed. The heading is `### PRD-<topic>: <outcome as a sentence>`, so a link to the heading anchor stays stable while
  the wording around it changes.
- **Outcome:** what is true for a user when the area is delivered, not a feature list.
- **Measure:** how the owner will tell the outcome is reached. Optional at level light.
- **In / Out:** the boundary of the area.
- **Status:** `planned` (committed, not started), `in-progress` (an open change serves it), `delivered`, or `dropped`
  (kept in the file with the reason, so the ID is not reused).

## Rules

- **The owner decides.** The product owner proposes edits; an edit to Purpose, Users, Non-goals or an area's Outcome
  needs the owner's yes. The commit that changes the PRD updates `updated`.
- **No behaviour detail.** Exact behaviour belongs in living specs; the PRD links to them where helpful.
- **Links:** a change's Intent and an idea's `prd` field name the area it serves by its ID.

## Index

The PRD is listed in the product index, `docs/product/README.md` (see [idea.md](idea.md)).

## Checked by

`keellay check` (task 4): front matter; every area heading has a unique `PRD-` ID; each area has Outcome, In / Out
and Status, and Measure at levels standard and strict; area IDs referenced from changes and ideas exist; an area
removed from the file is reported (it should be `dropped` instead).

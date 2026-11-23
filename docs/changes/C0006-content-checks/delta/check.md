---
capability: check
---

# Delta: check

## ADDED

### REQ-check-009: Phases

The CLI shall report, as check `phases`, every phase of an open change's plan (a `###` heading under `## Phases`)
that lacks a `Role`, `Depends on` or `Done when` line, whose role is neither a core role (`architect`, `developer`,
`product-owner`, `manager`) nor an instance of one (`<core role>-<qualifier>`), or that depends on a phase number the
plan does not have, and an open change past `draft` whose plan has no phase.

#### Scenario: phase without done-when

- GIVEN an open change whose phase 2 has `Role` and `Depends on` lines and no `Done when` line
- WHEN `keellay check` runs
- THEN there is a `phases` error for the plan that names phase 2 and `Done when`

#### Scenario: unknown role and an instance

- GIVEN an open change with one phase whose role is `tester` and another whose role is `developer-flutter`
- WHEN `keellay check` runs
- THEN there is a `phases` error that names `tester`
- AND there is no finding for `developer-flutter`

#### Scenario: plan without phases

- GIVEN an open change with `status: draft` and no phase heading, and another with `status: approved` and no phase
  heading
- WHEN `keellay check` runs
- THEN there is a `phases` error for the approved one
- AND there is no `phases` finding for the draft

#### Scenario: archived plan

- GIVEN a change in `docs/changes/archive/` whose phase has no `Done when` line
- WHEN `keellay check` runs
- THEN there is no `phases` finding for it

### REQ-check-010: Ideas

The CLI shall report, as check `ideas`, an idea with status `assessed` and no `verdict`; an idea with status
`planned`, `done` or `declined`, no `verdict` and an empty Assessment section; a `declined` idea with an empty Outcome
section; a `change` that names no change, open or archived; a `done` idea whose `change` names a change that is not
`closed`; and a `prd` that names no area of the PRD.

#### Scenario: assessed without a verdict

- GIVEN an idea with `status: assessed` and an empty `verdict`
- WHEN `keellay check` runs
- THEN there is an `ideas` error for that idea's file

#### Scenario: verdict skipped with a reason

- GIVEN an idea with `status: planned`, an empty `verdict` and an Assessment section that says why it was skipped
- WHEN `keellay check` runs
- THEN there is no `ideas` finding for it

#### Scenario: change that does not exist

- GIVEN an idea with `change: C0042-x` and no change `C0042-x` in `docs/changes/` or its archive
- WHEN `keellay check` runs
- THEN there is an `ideas` error that names `C0042-x`

#### Scenario: unknown PRD area

- GIVEN an idea with `prd: PRD-export` and a PRD without an area `PRD-export`
- WHEN `keellay check` runs
- THEN there is an `ideas` error that names `PRD-export`

### REQ-check-011: Lessons

The CLI shall report, as check `lessons`, a lesson whose `count` differs from the number of items under its
Occurrences heading; a `mechanized` lesson with an empty `mechanism`; and an `active` lesson with a `count` of 2 or
more whose last occurrence names a change by its ID (`C0007`) that is `closed` while that change's Decisions section
does not name the lesson by its ID (`L0003`), which is where the owner's waiver is recorded.

#### Scenario: count and occurrences disagree

- GIVEN a lesson with `count: 2` and three items under Occurrences
- WHEN `keellay check` runs
- THEN there is a `lessons` error for that lesson's file that names both numbers

#### Scenario: repeated lesson closed without a mechanism

- GIVEN an active lesson with `count: 2` whose last occurrence names change C0007, and change C0007 closed with no
  mention of the lesson in its Decisions
- WHEN `keellay check` runs
- THEN there is a `lessons` error for the lesson that names change C0007

#### Scenario: waived mechanism

- GIVEN the same lesson, and change C0007's Decisions name the lesson with the owner's waiver
- WHEN `keellay check` runs
- THEN there is no `lessons` finding for it

### REQ-check-012: Superseded ADRs

The CLI shall report, as check `adr`, an ADR whose `supersedes` names an ADR that does not name it back in
`superseded-by`, an ADR whose `superseded-by` names an ADR that does not name it in `supersedes`, an ADR with status
`superseded` and no `superseded-by`, and an ADR with a `superseded-by` whose status is not `superseded`.

#### Scenario: one side of the link missing

- GIVEN ADR A0012 with `supersedes: A0004`, and ADR A0004 with `status: superseded` and an empty `superseded-by`
- WHEN `keellay check` runs
- THEN there is an `adr` error for ADR A0004 that names A0012

#### Scenario: one ADR supersedes several

- GIVEN ADR A0012 with `supersedes: [A0004, A0007]`, and ADRs A0004 and A0007 both `superseded` by A0012
- WHEN `keellay check` runs
- THEN there is no `adr` finding

### REQ-check-013: PRD areas

The CLI shall report, as check `prd`, an area heading under `## Areas` that is not `### PRD-<topic>: <outcome>`, an
area ID used by two headings, an area without an Outcome, In / Out or Status line, a Status other than `planned`,
`in-progress`, `delivered` or `dropped`, an area without a Measure line at levels standard and strict, and a `PRD-`
ID named in an open change's plan that is not an area of the PRD.

#### Scenario: area without a status

- GIVEN a PRD whose area `PRD-limits` has Outcome, Measure and In / Out lines and no Status line
- WHEN `keellay check` runs
- THEN there is a `prd` error that names `PRD-limits` and `Status`

#### Scenario: measure by level

- GIVEN a PRD area without a Measure line
- WHEN `keellay check` runs at level light
- THEN there is no `prd` finding for it
- AND at level standard there is a `prd` error that names `Measure`

#### Scenario: plan names an unknown area

- GIVEN an open change whose Intent names `PRD-export`, and a PRD without that area
- WHEN `keellay check` runs
- THEN there is a `prd` error for the plan that names `PRD-export`

### REQ-check-014: Constitution

Where the project has a constitution section, the CLI shall report, as check `constitution`, a constitution file
missing at its resolved path, a constitution without one of the sections `Project`, `Owner`, `Read first` and
`Rules`, and an `AGENTS.md` that is missing or does not link to the constitution.

#### Scenario: missing section

- GIVEN a constitution without a `## Read first` section
- WHEN `keellay check` runs
- THEN there is a `constitution` error that names `Read first`

#### Scenario: AGENTS.md does not point to it

- GIVEN an `AGENTS.md` with no link to `docs/constitution.md`
- WHEN `keellay check` runs
- THEN there is a `constitution` error for `AGENTS.md`

#### Scenario: no constitution section

- GIVEN `.keellay/config.toml` with `constitution = false` under `[sections]`
- WHEN `keellay check` runs
- THEN there is no `constitution` finding

### REQ-check-015: Deltas against the spec

The CLI shall report, as check `deltas`, a requirement under MODIFIED or REMOVED of an open change's delta whose ID is
not in the living spec of the delta's capability, a requirement under ADDED whose ID is already in that spec, a delta
for a capability without a spec that has MODIFIED or REMOVED requirements or no `prefix`, and a requirement ID touched
by the deltas of two open changes, reported for both.

#### Scenario: modified requirement that does not exist

- GIVEN an open change whose delta `check` has `REQ-check-042` under MODIFIED, and a spec `check` without it
- WHEN `keellay check` runs
- THEN there is a `deltas` error for the delta that names `REQ-check-042`

#### Scenario: two open changes touch one requirement

- GIVEN two open changes whose deltas both have `REQ-check-003` under MODIFIED
- WHEN `keellay check` runs
- THEN there is a `deltas` error that names `REQ-check-003` and both changes

#### Scenario: archived delta

- GIVEN a delta in `docs/changes/archive/` whose ADDED requirement is now in the spec
- WHEN `keellay check` runs
- THEN there is no `deltas` finding for it

### REQ-check-016: Requirements

The CLI shall report, as check `requirements`, a requirement of a living spec, or under ADDED or MODIFIED of an open
change's delta, whose statement has no "shall" or that has no scenario with a WHEN and a THEN line, and at level
strict a requirement without a `Verified by` line or whose `Verified by` names a test file that does not exist.

#### Scenario: requirement without a scenario

- GIVEN a living spec with a requirement that has a statement with "shall" and no `#### Scenario:` heading
- WHEN `keellay check` runs
- THEN there is a `requirements` error that names the requirement

#### Scenario: Verified by at strict

- GIVEN level strict and a requirement whose `Verified by` names `tests/test_missing.py::test_x`, a file that does
  not exist
- WHEN `keellay check` runs
- THEN there is a `requirements` error that names `tests/test_missing.py`

#### Scenario: Verified by below strict

- GIVEN level standard and a requirement without a `Verified by` line
- WHEN `keellay check` runs
- THEN there is no `requirements` finding for it

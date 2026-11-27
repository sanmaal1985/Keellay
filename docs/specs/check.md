---
capability: check
prefix: check
---

# Check

The `keellay check` command: the checks that the formats in `method/formats/` name under "Checked by", run on a
project's artifacts from git hooks and CI. This spec covers front matter, numbers, indexes and links, and the rules
inside artifacts that can be read from the files themselves: phases of a plan, ideas, lessons, superseded ADRs, PRD
areas, the constitution, deltas and requirements. Checks against git history and the pull request are added by later
changes. Sections are found through `keellay paths`; a section that does not exist is skipped.

## Requirements

### REQ-check-001: Clean project

When `keellay check` runs in a project whose artifacts break none of the checks, the CLI shall report status `ok`
with an empty list of findings, and exit with code 0.

#### Scenario: nothing to report

- GIVEN a project whose artifacts follow their formats
- WHEN `keellay check` runs
- THEN the output is `{"command": "check", "status": "ok", "findings": []}`
- AND the exit code is 0

### REQ-check-002: Findings

If an artifact breaks a check, then the CLI shall report one finding per problem with the fields `check`, `severity`
(`error`, `warning` or `advice`), `file` (relative to the root, with `/`), `line` (a number, or null when the problem
is not on one line) and `message`; the status shall be `failed` and the exit code 1 when any finding is an error,
and `ok` with exit code 0 otherwise.

#### Scenario: one broken link

- GIVEN `docs/adr/README.md` links to `A0009-missing.md`, which does not exist
- WHEN `keellay check` runs
- THEN the output has `"status": "failed"` and a finding with `"check": "links"`, `"severity": "error"`,
  `"file": "docs/adr/README.md"` and the line of the link
- AND the exit code is 1

### REQ-check-003: Front matter

The CLI shall report, as check `front-matter`, every change plan, idea, ADR, lesson, PRD, living spec, delta and
constitution whose front matter is missing, is not valid YAML, lacks a field its format requires, has a value its format
does not allow, or has a number that does not match its file name. A number is the letter of its kind and at least four
digits, zero-padded to four: `C` for a change, `I` for an idea, `A` for an ADR, `L` for a lesson (`C0007`, `I0004`,
`A0012`, `L0003`). A change, idea, ADR or lesson whose file or folder name does not start with its number (for a change,
a folder that is not its change ID, `C0007-topic`, also one that holds only deltas), a number field (`id`, `supersedes`,
`superseded-by`) and an idea's `change`, a change ID, that is bare (`0012`), carries another kind's letter or pads past
four digits (`A00012`), are reported. Values are read as strings, so `A0012` stays `A0012`.

#### Scenario: unknown status

- GIVEN an idea whose front matter has `status: started`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that idea's file that names `started`

#### Scenario: number and file name disagree

- GIVEN `docs/lessons/L0003-x.md` whose front matter has `id: L0004`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that file

#### Scenario: number past 9999

- GIVEN `docs/product/ideas/I10000-x.md` whose front matter has `id: I10000`
- WHEN `keellay check` runs
- THEN there is no `front-matter` finding for that file

#### Scenario: bare number

- GIVEN `docs/adr/0012-x.md` whose front matter has `id: 0012`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that file that names the expected form `A0012`

#### Scenario: another kind's letter

- GIVEN `docs/adr/A0013-x.md` whose front matter has `supersedes: C0004`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that file

### REQ-check-004: Unique numbers

The CLI shall report, as check `numbers`, a number used by two changes (open or archived), two ideas, two ADRs or two
lessons, and a requirement ID that appears twice in a living spec or does not use its spec's prefix.

#### Scenario: two changes with one number

- GIVEN `docs/changes/C0007-a/` and `docs/changes/archive/C0007-b/`
- WHEN `keellay check` runs
- THEN there is a `numbers` error that names both folders

#### Scenario: one number, two kinds

- GIVEN `docs/changes/C0006-a/` and `docs/product/ideas/I0006-b.md`
- WHEN `keellay check` runs
- THEN there is no `numbers` finding: each kind counts on its own

### REQ-check-005: Indexes

The CLI shall report, as check `index`, an item that its section's index does not list, lists twice, lists in a table
that does not match its status, or lists with a status other than its own, and an index row that points to no item;
the changes index lists exactly the open changes.

#### Scenario: idea in the wrong table

- GIVEN an idea with `status: declined` listed among the open ideas of the register
- WHEN `keellay check` runs
- THEN there is an `index` error for the register that names the idea

#### Scenario: closed change still listed

- GIVEN a change in `docs/changes/archive/` that still has a row in `docs/changes/README.md`
- WHEN `keellay check` runs
- THEN there is an `index` error for that row

### REQ-check-006: Links

The CLI shall report, as check `links`, every relative link that points to no existing file or folder in `AGENTS.md`,
in the Markdown files of the project's sections and in the Markdown files and folders listed in `links` under `[check]`
in `.keellay/config.toml`; links inside fenced code blocks and inline code, links with a URL scheme and links that
leave the project root are not checked, and the part after `#` is ignored.

#### Scenario: extra paths from the config

- GIVEN `.keellay/config.toml` with `links = ["method", "README.md"]` under `[check]`, and `method/formats/adr.md`
  that links to `missing.md` outside a code block
- WHEN `keellay check` runs
- THEN there is a `links` error for `method/formats/adr.md`

#### Scenario: link in an example

- GIVEN a fenced code block in a format file that links to `docs/changes/C0007-x/plan.md`, which does not exist
- WHEN `keellay check` runs
- THEN there is no `links` finding for that link

### REQ-check-007: Staged content

When invoked with `--staged` in a git repository, the CLI shall check the files and read `.keellay/config.toml` as they
are in the git index, and treat files that are not in the index as absent.

#### Scenario: unfinished file of another session

- GIVEN a staged change that follows its format, and an unstaged edit in another file that breaks a link
- WHEN `keellay check --staged` runs
- THEN the status is `ok`

#### Scenario: config edited but not staged

- GIVEN an unstaged edit of `.keellay/config.toml` that maps a section to another folder
- WHEN `keellay check --staged` runs
- THEN the sections are those of the staged config

### REQ-check-008: Invalid config

If `.keellay/config.toml` is invalid as described in REQ-paths-004, or its `links` under `[check]` is not a list of
paths, then `keellay check` shall report status `error` with a message that names the problem and no findings, and
exit with code 2.

#### Scenario: config with an unknown section

- GIVEN `.keellay/config.toml` that maps a section `tasks`
- WHEN `keellay check` runs
- THEN the output has `"status": "error"` and a message that names `tasks`
- AND the exit code is 2

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
`closed`; and a `prd` that names no area of the PRD; where the project's `changes` section is outside its root, the
CLI shall not check an idea's `change`.

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

#### Scenario: plans in another repository

- GIVEN a project whose `changes` section is `../other/changes`, and a `done` idea with `change: C0042-x`
- WHEN `keellay check` runs
- THEN there is no `ideas` finding for it

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
`superseded` and no `superseded-by`, an ADR with a `superseded-by` whose status is not `superseded`, and an ADR
that names itself in `supersedes` or `superseded-by`.

#### Scenario: one side of the link missing

- GIVEN ADR A0012 with `supersedes: A0004`, and ADR A0004 with `status: superseded` and an empty `superseded-by`
- WHEN `keellay check` runs
- THEN there is an `adr` error for ADR A0004 that names A0012

#### Scenario: one ADR supersedes several

- GIVEN ADR A0012 with `supersedes: [A0004, A0007]`, and ADRs A0004 and A0007 both `superseded` by A0012
- WHEN `keellay check` runs
- THEN there is no `adr` finding

#### Scenario: ADR that supersedes itself

- GIVEN an ADR `A0001` with `supersedes: A0001`
- WHEN `keellay check` runs
- THEN there is an `adr` error that says `A0001` names itself

### REQ-check-013: PRD areas

The CLI shall report, as check `prd`, an area heading under `## Areas` that is not `### PRD-<topic>: <outcome>`, an
area ID used by two headings, an area without an Outcome, In / Out or Status line, a Status whose first word is not
`planned`, `in-progress`, `delivered` or `dropped`, an area without a Measure line at levels standard and strict, and
a `PRD-` ID named in an open change's plan that is not an area of the PRD; an ID right after `/`, as in a URL or a
path, is not one the plan names, unless the `/` joins it to an ID the plan names (`PRD-a/PRD-b` names both).

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
`Rules`, and an `AGENTS.md` that is missing or does not link to the constitution; where the constitution section is
outside the project's root, the CLI shall check neither the constitution nor `AGENTS.md`.

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

#### Scenario: constitution in another repository

- GIVEN `.keellay/config.toml` with `constitution = "../other/docs/constitution.md"` under
  `[sections]`, and no `AGENTS.md`
- WHEN `keellay check` runs
- THEN there is no `constitution` finding

### REQ-check-015: Deltas against the spec

The CLI shall report, as check `deltas`, a requirement under MODIFIED or REMOVED of an open change's delta whose ID is
not in the living spec of the delta's capability, a requirement under ADDED whose ID is already in that spec, a delta
for a capability without a spec that has MODIFIED or REMOVED requirements or no `prefix`, a `##` section of a delta
other than `ADDED`, `MODIFIED`, `REMOVED` and `Purpose`, and a requirement ID touched by the deltas of two open
changes, reported for both; where the project's `specs` section is outside its root, the CLI shall not check
deltas.

#### Scenario: modified requirement that does not exist

- GIVEN an open change whose delta `check` has `REQ-check-042` under MODIFIED, and a spec `check` without it
- WHEN `keellay check` runs
- THEN there is a `deltas` error for the delta that names `REQ-check-042`

#### Scenario: two open changes touch one requirement

- GIVEN two open changes whose deltas both have `REQ-check-003` under MODIFIED
- WHEN `keellay check` runs
- THEN there is a `deltas` error that names `REQ-check-003` and both changes

#### Scenario: unknown section

- GIVEN an open change whose delta has a section `## Added`
- WHEN `keellay check` runs
- THEN there is a `deltas` error at that heading that names `## Added`

#### Scenario: archived delta

- GIVEN a delta in `docs/changes/archive/` whose ADDED requirement is now in the spec
- WHEN `keellay check` runs
- THEN there is no `deltas` finding for it

#### Scenario: specs in another repository

- GIVEN `.keellay/config.toml` with `specs = "../other/docs/specs"` under `[sections]`, and an
  open change whose delta has `REQ-check-042` under MODIFIED
- WHEN `keellay check` runs
- THEN there is no `deltas` finding

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

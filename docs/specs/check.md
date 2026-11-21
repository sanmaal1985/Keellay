---
capability: check
prefix: check
---

# Check

The `keellay check` command: the checks that the formats in `method/formats/` name under "Checked by", run on a
project's artifacts from git hooks and CI. This spec covers front matter, numbers, indexes and links; the other checks
the formats name are added by later changes. Sections are found through `keellay paths`; a section that does not
exist is skipped.

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

- GIVEN `docs/adr/README.md` links to `0009-missing.md`, which does not exist
- WHEN `keellay check` runs
- THEN the output has `"status": "failed"` and a finding with `"check": "links"`, `"severity": "error"`,
  `"file": "docs/adr/README.md"` and the line of the link
- AND the exit code is 1

### REQ-check-003: Front matter

The CLI shall report, as check `front-matter`, every change plan, idea, ADR, lesson, PRD, living spec, delta and
constitution whose front matter is missing, is not valid YAML, lacks a field its format requires, has a value its
format does not allow, or has a number that does not match its file name; values are read as strings, so `0012`
stays `0012`.

#### Scenario: unknown status

- GIVEN an idea whose front matter has `status: started`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that idea's file that names `started`

#### Scenario: number and file name disagree

- GIVEN `docs/lessons/0003-x.md` whose front matter has `id: 0004`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that file

### REQ-check-004: Unique numbers

The CLI shall report, as check `numbers`, a number used by two changes (open or archived), two ideas, two ADRs or two
lessons, and a requirement ID that appears twice in a living spec or does not use its spec's prefix.

#### Scenario: two changes with one number

- GIVEN `docs/changes/0007-a/` and `docs/changes/archive/0007-b/`
- WHEN `keellay check` runs
- THEN there is a `numbers` error that names both folders

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

- GIVEN a fenced code block in a format file that links to `docs/changes/0007-x/plan.md`, which does not exist
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

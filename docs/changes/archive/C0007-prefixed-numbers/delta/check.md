---
capability: check
---

# Delta: check

## MODIFIED

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
constitution whose front matter is missing, is not valid YAML, lacks a field its format requires, has a value its
format does not allow, or has a number that does not match its file name. A number is the letter of its kind and four
digits: `C` for a change, `I` for an idea, `A` for an ADR, `L` for a lesson (`C0007`, `I0026`, `A0037`, `L0013`); a
change, idea, ADR or lesson whose file or folder name does not start with its number, and a number field (`id`,
`supersedes`, `superseded-by`, an idea's `change`) that is bare (`0012`) or carries another kind's letter, are
reported. Values are read as strings, so `A0012` stays `A0012`.

#### Scenario: unknown status

- GIVEN an idea whose front matter has `status: started`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that idea's file that names `started`

#### Scenario: number and file name disagree

- GIVEN `docs/lessons/L0003-x.md` whose front matter has `id: L0004`
- WHEN `keellay check` runs
- THEN there is a `front-matter` error for that file

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

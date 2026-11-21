---
capability: paths
prefix: paths
---

# Delta: paths

## Purpose

The `keellay paths` command: where a project's root is, which level it runs at and where each artifact section
lives, from the defaults in `method/layout.md` and the project's `.keellay/config.toml`. Checks and other commands
find sections only through it. The sections are `constitution` (a file), `product`, `specs`, `changes`, `adr` and
`lessons`.

## ADDED

### REQ-paths-001: Project root

The CLI shall take as the project root the top-level folder of the git repository it runs in, or the current folder
when it runs outside a git repository.

#### Scenario: run from a subfolder

- GIVEN a git repository with the folder `docs/adr`
- WHEN `keellay paths` runs in `docs/adr`
- THEN `root` is the repository's top-level folder

### REQ-paths-002: Defaults without a config

When `keellay paths` runs in a project without `.keellay/config.toml`, the CLI shall report status `ok`, the root,
the level `standard` and every section at its default path from `method/layout.md` with whether it exists, and exit
with code 0.

#### Scenario: default layout

- GIVEN a project with `docs/adr/` and no `.keellay/config.toml`
- WHEN `keellay paths` runs
- THEN the output has `"level": "standard"`
- AND `sections.adr` is `{"path": "docs/adr", "exists": true}`
- AND `sections.lessons` is `{"path": "docs/lessons", "exists": false}`

### REQ-paths-003: Config overrides

Where `.keellay/config.toml` sets `level` or maps a section in its `[sections]` table, the CLI shall report that level
and that path, relative to the root, in place of the default; a section mapped to `false` is reported as
`{"path": null, "exists": false}`.

#### Scenario: specs in another repository, no lessons

- GIVEN `.keellay/config.toml` with `level = "light"`, `specs = "../other/docs/specs"` and `lessons = false` under
  `[sections]`
- WHEN `keellay paths` runs
- THEN the output has `"level": "light"`
- AND `sections.specs.path` is `../other/docs/specs`
- AND `sections.lessons` is `{"path": null, "exists": false}`

### REQ-paths-004: Invalid config

If `.keellay/config.toml` cannot be parsed, names an unknown level or section, or gives a section a value that is
neither a path nor `false`, then the CLI shall report status `error` with a message that names the problem, and exit
with code 2.

#### Scenario: unknown level

- GIVEN `.keellay/config.toml` with `level = "medium"`
- WHEN `keellay paths` runs
- THEN the output has `"status": "error"` and a message that names `medium`
- AND the exit code is 2

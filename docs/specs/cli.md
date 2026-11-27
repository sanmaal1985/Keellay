---
capability: cli
prefix: cli
---

# CLI

The `keellay` command: how it reports its version, the shape of its output, the `info` command and the commands that
exist in the interface but are not built yet. What each command does once built is specified with it.

## Requirements

### REQ-cli-001: Version

When invoked with `--version`, the CLI shall print `keellay <version>` and exit with code 0.

Verified by: `tests/test_cli.py::test_version`

#### Scenario: version flag

- WHEN `keellay --version` runs
- THEN the output is `keellay ` followed by the installed package version
- AND the exit code is 0

### REQ-cli-002: One JSON object per command

The CLI shall print the result of every command as one JSON object on one line of standard output, with the fields
`command` and `status`, in ASCII, with every other character written as a `\u` escape.

Verified by: `tests/test_cli.py::test_info_finds_the_method`,
`tests/test_cli.py::test_planned_commands_report_not_implemented`,
`tests/test_cli.py::test_output_is_ascii_with_escapes`

#### Scenario: any command

- WHEN any command runs
- THEN standard output is one line that parses as a JSON object
- AND the object has `command` set to the command's name and a `status`

#### Scenario: a character outside ASCII

- GIVEN a project whose root path contains `ё`
- WHEN `keellay paths` runs
- THEN standard output contains only ASCII characters, with `ё` written as `\u0451`
- AND the parsed `root` contains `ё`

### REQ-cli-003: Info

When invoked with `info`, the CLI shall report status `ok`, its version, the method directory and whether that
directory is the copy bundled in the installed package, and exit with code 0.

Verified by: `tests/test_cli.py::test_info_finds_the_method`

#### Scenario: info from a source checkout

- GIVEN Keellay runs from a source checkout or an editable install
- WHEN `keellay info` runs
- THEN `method_dir` is the repository's `method/` folder and `method_bundled` is false

### REQ-cli-004: Method bundled in the package

Where Keellay is installed from a wheel, the CLI shall read the method from the copy inside the installed package.

Verified by: `tests/check_wheel.py`

#### Scenario: installed wheel

- GIVEN the wheel is installed in an environment without the source tree
- WHEN `keellay info` runs
- THEN `method_bundled` is true and `method_dir` contains the method's `README.md`

### REQ-cli-005: Commands not built yet

When invoked with `init`, the CLI shall report status `not_implemented` with a description of the planned command,
and exit with code 3.

Verified by: `tests/test_cli.py::test_planned_commands_report_not_implemented`

#### Scenario: planned command

- WHEN `keellay init` runs
- THEN the output is `{"command": "init", "status": "not_implemented", "message": ...}`
- AND the exit code is 3

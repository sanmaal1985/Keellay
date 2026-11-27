---
capability: cli
---

# Delta: cli

## MODIFIED

### REQ-cli-002: One JSON object per command

The CLI shall print the result of every command as one JSON object on one line of standard output, with the fields
`command` and `status`, in ASCII, with every other character written as a `\u` escape.

Verified by: `tests/test_cli.py::test_info_finds_the_method`,
`tests/test_cli.py::test_planned_commands_report_not_implemented`, `tests/test_cli.py::test_output_is_ascii_with_escapes`

#### Scenario: any command

- WHEN any command runs
- THEN standard output is one line that parses as a JSON object
- AND the object has `command` set to the command's name and a `status`

#### Scenario: a character outside ASCII

- GIVEN a project whose root path contains `ё`
- WHEN `keellay paths` runs
- THEN standard output contains only ASCII characters, with `ё` written as `ё`
- AND the parsed `root` contains `ё`

---
capability: cli
---

# Delta: cli

## MODIFIED

### REQ-cli-005: Commands not built yet

When invoked with `init`, the CLI shall report status `not_implemented` with a description of the planned command,
and exit with code 3.

Verified by: `tests/test_cli.py::test_planned_commands_report_not_implemented`

#### Scenario: planned command

- WHEN `keellay init` runs
- THEN the output is `{"command": "init", "status": "not_implemented", "message": ...}`
- AND the exit code is 3

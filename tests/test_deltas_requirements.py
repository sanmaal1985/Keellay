"""Scenarios of REQ-check-015 and 016 as tests: an open change's delta agrees with its spec and no requirement is
touched by two open changes; requirements have a "shall" statement and a scenario, and at level strict a test that
verifies them."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import main


def run_check(root: Path, capsys, monkeypatch):
    monkeypatch.chdir(root)
    code = main(["check"])
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def of(out: dict, check: str) -> list[dict]:
    return [finding for finding in out["findings"] if finding["check"] == check]


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


SCENARIO = "#### Scenario: it works\n\n- GIVEN a thing\n- WHEN it runs\n- THEN it works\n"


def requirement(req_id: str, statement: str = "The CLI shall do it.", verified_by: str = "",
                scenario: str = SCENARIO) -> str:
    text = f"### {req_id}: Title\n\n{statement}\n\n"
    if verified_by:
        text += f"{verified_by}\n\n"
    return text + (f"{scenario}\n" if scenario else "")


def spec(*requirements: str, capability: str = "check") -> str:
    return (f"---\ncapability: {capability}\nprefix: {capability}\n---\n\n# Check\n\nWhat it is.\n\n"
            f"## Requirements\n\n" + "".join(requirements))


def delta(sections: dict[str, list[str]], capability: str = "check", prefix: str = "") -> str:
    text = f"---\ncapability: {capability}\n" + (f"prefix: {prefix}\n" if prefix else "") + "---\n\n"
    text += f"# Delta: {capability}\n\n"
    for title, requirements in sections.items():
        text += f"## {title}\n\n" + "".join(requirements)
    return text


SPEC = "docs/specs/check.md"


def removed(req_id: str) -> str:
    return f"### {req_id}: Title\n\nReason: replaced.\n\n"


# REQ-check-015: deltas against the spec


def test_modified_requirement_that_does_not_exist(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/C0001-x/delta/check.md", delta({"MODIFIED": [requirement("REQ-check-042")]}))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "deltas")
    assert finding["severity"] == "error" and finding["file"] == "docs/changes/C0001-x/delta/check.md"
    assert "REQ-check-042" in finding["message"] and code == 1


def test_removed_requirement_that_does_not_exist(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/C0001-x/delta/check.md", delta({"REMOVED": [removed("REQ-check-007")]}))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "deltas")
    assert "REQ-check-007 is under REMOVED" in finding["message"]


def test_two_open_changes_touch_one_requirement(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-003")))
    write(project, "docs/changes/C0001-x/delta/check.md", delta({"MODIFIED": [requirement("REQ-check-003")]}))
    write(project, "docs/changes/C0002-y/delta/check.md", delta({"MODIFIED": [requirement("REQ-check-003")]}))
    code, out = run_check(project, capsys, monkeypatch)
    findings = of(out, "deltas")
    assert sorted(finding["file"] for finding in findings) == ["docs/changes/C0001-x/delta/check.md",
                                                               "docs/changes/C0002-y/delta/check.md"]
    assert all("REQ-check-003" in finding["message"] for finding in findings)
    assert "C0002-y" in findings[0]["message"] and "C0001-x" in findings[1]["message"]


def test_archived_delta(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/archive/C0001-x/delta/check.md", delta({"ADDED": [requirement("REQ-check-001")]}))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "deltas") == []


def test_added_requirement_already_in_the_spec(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/C0001-x/delta/check.md",
          delta({"ADDED": [requirement("REQ-check-001"), requirement("REQ-check-002")]}))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "deltas")
    assert "REQ-check-001 is under ADDED" in finding["message"] and SPEC in finding["message"]


def test_new_capability_without_prefix(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/C0001-x/delta/export.md",
          delta({"ADDED": [requirement("REQ-export-001")]}, capability="export"))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "deltas")
    assert "`prefix`" in finding["message"] and finding["line"] == 2  # the capability line


def test_new_capability_with_prefix_that_only_adds(capsys, monkeypatch, project):
    write(project, "docs/changes/C0001-x/delta/export.md",
          delta({"ADDED": [requirement("REQ-export-001")]}, capability="export", prefix="export"))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "deltas") == []


def test_new_capability_that_modifies(capsys, monkeypatch, project):
    write(project, "docs/changes/C0001-x/delta/export.md",
          delta({"MODIFIED": [requirement("REQ-export-001")]}, capability="export", prefix="export"))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "deltas")
    assert "has no spec yet" in finding["message"]


def test_capability_is_read_from_the_file_name_without_front_matter_field(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001")))
    write(project, "docs/changes/C0001-x/delta/check.md",
          "---\n---\n\n# Delta\n\n## MODIFIED\n\n" + requirement("REQ-check-001"))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "deltas") == []


def test_specs_in_another_repository_are_not_checked_here(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", '[sections]\nspecs = "../other/docs/specs"\n')
    write(project, "docs/changes/C0001-x/delta/check.md", delta({"MODIFIED": [requirement("REQ-check-042")]}))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "deltas") == []


# REQ-check-016: requirements


def test_requirement_without_a_scenario(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001", scenario="")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert finding["severity"] == "error" and "REQ-check-001" in finding["message"]
    assert finding["file"] == SPEC and finding["line"] == 12  # the requirement heading


def test_scenario_with_then_and_no_when(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001", scenario="#### Scenario: x\n\n- GIVEN a\n- THEN b\n")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert "no scenario with a WHEN and a THEN line" in finding["message"]


def test_one_whole_scenario_is_enough(capsys, monkeypatch, project):
    half = "#### Scenario: half\n\n- THEN b\n\n"
    write(project, SPEC, spec(requirement("REQ-check-001", scenario=half + SCENARIO)))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "requirements") == []


def test_statement_without_shall(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001", statement="The CLI does it.")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert '"shall"' in finding["message"]


def test_shall_inside_a_scenario_is_not_a_statement(capsys, monkeypatch, project):
    scenario = "#### Scenario: x\n\n- WHEN it runs\n- THEN it shall work\n"
    write(project, SPEC, spec(requirement("REQ-check-001", statement="The CLI does it.", scenario=scenario)))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert '"shall"' in finding["message"]


def test_verified_by_at_strict(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", 'level = "strict"\n')
    write(project, SPEC, spec(requirement("REQ-check-001", verified_by="Verified by: `tests/test_missing.py::test_x`")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert "tests/test_missing.py" in finding["message"] and finding["line"] == 16  # the Verified by line


def test_verified_by_below_strict(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", 'level = "standard"\n')
    write(project, SPEC, spec(requirement("REQ-check-001")))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "requirements") == []


def test_no_verified_by_at_strict(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", 'level = "strict"\n')
    write(project, SPEC, spec(requirement("REQ-check-001")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert "`Verified by`" in finding["message"] and "strict" in finding["message"]


def test_wrapped_verified_by_with_existing_tests(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", 'level = "strict"\n')
    write(project, "tests/test_a.py", "")
    write(project, "tests/test_b.py", "")
    verified = "Verified by: `tests/test_a.py::test_x`,\n`tests/test_b.py::test_y`"
    write(project, SPEC, spec(requirement("REQ-check-001", verified_by=verified)))
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "requirements") == []
    write(project, SPEC, spec(requirement("REQ-check-001", verified_by=verified.replace("test_b", "test_c"))))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert "tests/test_c.py" in finding["message"]


def test_delta_requirements_are_checked_except_removed(capsys, monkeypatch, project):
    write(project, SPEC, spec(requirement("REQ-check-001"), requirement("REQ-check-002")))
    write(project, "docs/changes/C0001-x/delta/check.md",
          delta({"ADDED": [requirement("REQ-check-003", scenario="")], "REMOVED": [removed("REQ-check-002")]}))
    write(project, "docs/changes/archive/C0000-old/delta/check.md",
          delta({"ADDED": [requirement("REQ-check-001", statement="Old text.")]}))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "requirements")
    assert finding["file"] == "docs/changes/C0001-x/delta/check.md" and "REQ-check-003" in finding["message"]


def test_requirement_in_a_code_block_is_an_example(capsys, monkeypatch, project):
    example = "```markdown\n### REQ-check-009: Example\n\nNo statement.\n```\n\n"
    write(project, SPEC, spec(requirement("REQ-check-001")) + example)
    code, out = run_check(project, capsys, monkeypatch)
    assert of(out, "requirements") == []

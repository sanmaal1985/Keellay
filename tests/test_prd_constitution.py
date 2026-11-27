"""Scenarios of REQ-check-013 and 014 as tests: PRD areas keep their form, lines and status, plans name real areas,
and the constitution has its sections and is pointed to from `AGENTS.md`."""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from keellay.cli import main
from tests.helpers import CONSTITUTION, add_constitution

PRD = "docs/product/prd.md"


def run_check(root: Path, capsys, monkeypatch):
    monkeypatch.chdir(root)
    code = main(["check"])
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def of(out: dict[str, Any], check: str) -> list[dict[str, Any]]:
    return [finding for finding in out["findings"] if finding["check"] == check]


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    add_constitution(tmp_path)
    return tmp_path


def area(heading: str = "PRD-limits: Limits hold", outcome=True, measure=True, in_out=True, status="planned") -> str:
    lines = [f"### {heading}", ""]
    if outcome:
        lines.append("- Outcome: the keeper sees a limit coming.")
    if measure:
        lines.append("- Measure: share of months without a surprise.")
    if in_out:
        lines.append("- In: monthly limits. Out: yearly ones.")
    if status is not None:
        lines.append(f"- Status: {status}")
    return "\n".join(lines) + "\n\n"


def prd(*areas: str) -> str:
    return (
        "---\nproduct: X\nupdated: 2026-11-21\n---\n\n# X\n\n## Purpose\n\nP.\n\n## Areas\n\n"
        + "".join(areas)
        + "## Notes\n\n### PRD-outside: not an area, it is not under Areas\n"
    )


def plan(change_id: str, intent: str, status: str = "in-progress") -> str:
    return (
        f"---\nid: {change_id}\ntitle: T\npath: change\nstatus: {status}\napproved: 2026-11-21\n---\n\n# T\n\n"
        f"## Intent\n\n{intent}\n\n## Phases\n\n### 1. One\n\n- Role: developer\n- Depends on: —\n"
        f"- Done when: it works\n"
    )


# REQ-check-013: PRD areas


def test_area_without_a_status(capsys, monkeypatch, project):
    write(project, PRD, prd(area(status=None)))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert finding["severity"] == "error" and finding["file"] == PRD
    assert "PRD-limits" in finding["message"] and "`Status`" in finding["message"]


def test_measure_by_level(capsys, monkeypatch, project):
    write(project, PRD, prd(area(measure=False)))
    write(project, ".keellay/config.toml", 'level = "light"\n')
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "prd") == []
    write(project, ".keellay/config.toml", 'level = "standard"\n')
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert finding["severity"] == "error" and "`Measure`" in finding["message"]


def test_plan_names_an_unknown_area(capsys, monkeypatch, project):
    write(project, PRD, prd(area()))
    write(project, "docs/changes/C0001-x/plan.md", plan("C0001-x", "Serves PRD-limits and `PRD-export`."))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert finding["file"] == "docs/changes/C0001-x/plan.md" and "PRD-export" in finding["message"]
    assert finding["line"] == 13  # the Intent line


def test_archived_plan_and_code_examples_are_not_read_for_areas(capsys, monkeypatch, project):
    write(project, PRD, prd(area()))
    write(project, "docs/changes/archive/C0001-x/plan.md", plan("C0001-x", "Served PRD-gone.", status="closed"))
    write(project, "docs/changes/C0002-y/plan.md", plan("C0002-y", "```\nprd: PRD-example\n```"))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "prd") == []


def test_two_headings_with_one_area_id(capsys, monkeypatch, project):
    write(project, PRD, prd(area(), area("PRD-limits: Limits hold again")))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert "PRD-limits is used by two headings" in finding["message"]


@pytest.mark.parametrize("status", ["done", "`planned`x"])
def test_status_outside_the_four_values(capsys, monkeypatch, project, status):
    write(project, PRD, prd(area(status=status)))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert "Status is" in finding["message"] and "expected one of" in finding["message"]


def test_status_in_backticks_is_read(capsys, monkeypatch, project):
    write(project, PRD, prd(area(status="`in-progress`")))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "prd") == []


def test_reason_after_the_status_is_allowed(capsys, monkeypatch, project):
    write(project, PRD, prd(area(status="dropped — no demand")))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "prd") == []


def test_unknown_first_word_of_the_status_is_reported(capsys, monkeypatch, project):
    write(project, PRD, prd(area(status="abandoned — no demand")))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert "Status is `abandoned`" in finding["message"]


def test_area_id_inside_a_url_is_not_an_area_the_plan_names(capsys, monkeypatch, project):
    write(project, PRD, prd(area()))
    write(
        project,
        "docs/changes/C0001-x/plan.md",
        plan("C0001-x", "Serves PRD-limits; see https://example.com/PRD-foo/x and docs/PRD-bar.md."),
    )
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "prd") == []


def test_area_id_joined_by_a_slash_to_another_is_read(capsys, monkeypatch, project):
    write(project, PRD, prd(area()))
    write(
        project,
        "docs/changes/C0001-x/plan.md",
        plan("C0001-x", "Serves PRD-limits/PRD-limitz; see https://example.com/PRD-foo/PRD-bar."),
    )
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert "PRD-limitz" in finding["message"]


@pytest.mark.parametrize("status, shown", [("", "Status is empty;"), ("`planned`x", "Status is `` planned`x ``;")])
def test_status_message_keeps_its_quotes_whole(capsys, monkeypatch, project, status, shown):
    write(project, PRD, prd(area(status=status)))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert shown in finding["message"]


def test_heading_that_is_not_an_area_id(capsys, monkeypatch, project):
    write(project, PRD, prd(area("Limits: Limits hold")))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "prd")
    assert "`### PRD-<topic>: <outcome>`" in finding["message"]


def test_area_without_outcome_or_in_out(capsys, monkeypatch, project):
    write(project, PRD, prd(area(outcome=False, in_out=False)))
    _, out = run_check(project, capsys, monkeypatch)
    messages = sorted(finding["message"] for finding in of(out, "prd"))
    assert messages == ["PRD-limits has no `In / Out` line", "PRD-limits has no `Outcome` line"]


# REQ-check-014: constitution


def test_missing_section(capsys, monkeypatch, project):
    write(project, "docs/constitution.md", CONSTITUTION.replace("## Read first", "## Reading"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "constitution")
    assert finding["severity"] == "error" and "Read first" in finding["message"]


def test_agents_md_does_not_point_to_it(capsys, monkeypatch, project):
    write(project, "AGENTS.md", "Read [the rules](docs/rules.md).\n")
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "constitution")
    assert finding["file"] == "AGENTS.md"


def test_no_constitution_section(capsys, monkeypatch, project):
    (project / "docs" / "constitution.md").unlink()
    (project / "AGENTS.md").unlink()
    write(project, ".keellay/config.toml", "[sections]\nconstitution = false\n")
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "constitution") == []


def test_agents_md_links_to_a_mapped_constitution(capsys, monkeypatch, tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    add_constitution(tmp_path, "rules/constitution.md")
    write(tmp_path, ".keellay/config.toml", '[sections]\nconstitution = "rules/constitution.md"\n')
    write(tmp_path, "AGENTS.md", "Before any work, read [the constitution](./rules/constitution.md#rules).\n")
    _, out = run_check(tmp_path, capsys, monkeypatch)
    assert of(out, "constitution") == []


def test_constitution_missing_at_its_path(capsys, monkeypatch, project):
    (project / "docs" / "constitution.md").unlink()
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "constitution")
    assert finding["file"] == "docs/constitution.md" and "missing" in finding["message"]
    assert "expected at docs/constitution.md" in finding["message"]
    assert "method/formats/constitution.md in the Keellay repository" in finding["message"]


def test_agents_md_missing(capsys, monkeypatch, project):
    (project / "AGENTS.md").unlink()
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "constitution")
    assert finding["file"] == "AGENTS.md" and "missing" in finding["message"]
    assert "method/formats/constitution.md in the Keellay repository" in finding["message"]
    assert "shape of both files" in finding["message"]


def test_constitution_in_another_repository(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", '[sections]\nconstitution = "../other/docs/constitution.md"\n')
    (project / "AGENTS.md").unlink()
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "constitution") == []

"""Scenarios of REQ-check-009 as tests: every phase of an open change's plan has its fields and a known role."""

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


def phase(number: int, role: str | None = "developer", depends: str | None = "—", done: str | None = "it works") -> str:
    lines = [f"### {number}. Phase {number}", ""]
    if role is not None:
        lines.append(f"- Role: {role}")
    if depends is not None:
        lines.append(f"- Depends on: {depends}")
    if done is not None:
        lines.append(f"- Done when: {done}")
    return "\n".join(lines) + "\n\n"


def plan(change_id: str, *phases: str, status: str = "in-progress") -> str:
    head = f"---\nid: {change_id}\ntitle: T\npath: feature\nstatus: {status}\napproved: 2026-11-21\n---\n\n# T\n\n"
    return head + "## Phases\n\n" + "".join(phases) + "## Open questions\n\n- none\n"


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def phases_findings(out: dict) -> list[dict]:
    return [finding for finding in out["findings"] if finding["check"] == "phases"]


def test_phase_without_done_when(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a", phase(1), phase(2, depends="1", done=None)))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert code == 1
    assert finding["severity"] == "error" and finding["file"] == "docs/changes/C0007-a/plan.md"
    assert "phase 2" in finding["message"] and "Done when" in finding["message"]


def test_unknown_role_and_an_instance(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md",
          plan("C0007-a", phase(1, role="tester"), phase(2, role="developer-flutter", depends="1")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert "`tester`" in finding["message"]
    assert "developer-flutter" not in finding["message"]


def test_archived_plan(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0007-a/plan.md", plan("C0007-a", phase(1, done=None), status="closed"))
    code, out = run_check(project, capsys, monkeypatch)
    assert phases_findings(out) == []


def test_plan_without_phases(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a", status="draft"))
    write(project, "docs/changes/C0008-b/plan.md", plan("C0008-b", status="approved"))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert finding["file"] == "docs/changes/C0008-b/plan.md"
    assert "approved" in finding["message"]


def test_plan_without_a_phases_section(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md",
          "---\nid: C0007-a\ntitle: T\npath: change\nstatus: in-progress\napproved: 2026-11-21\n---\n\n# T\n")
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert finding["line"] is None


def test_depends_on_a_missing_phase(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a", phase(1), phase(2, depends="1, 3")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert "phase 2 depends on phase 3" in finding["message"]


def test_complete_plan_has_no_finding(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md",
          plan("C0007-a", phase(1, role="architect"), phase(2, role="`product-owner`", depends="1"),
               phase(3, role="manager", depends="1, 2")))
    code, out = run_check(project, capsys, monkeypatch)
    assert phases_findings(out) == []


def test_fields_in_a_code_block_or_nested_do_not_count(capsys, monkeypatch, project):
    nested = "### 1. Phase 1\n\n- Steps:\n  - Role: developer\n\n```markdown\n- Depends on: —\n```\n\n"
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a", nested))
    code, out = run_check(project, capsys, monkeypatch)
    messages = sorted(finding["message"] for finding in phases_findings(out))
    assert len(messages) == 3


def test_core_role_with_an_empty_qualifier_is_unknown(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a", phase(1, role="developer-")))
    code, out = run_check(project, capsys, monkeypatch)
    [finding] = phases_findings(out)
    assert "`developer-`" in finding["message"]

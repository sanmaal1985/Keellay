"""Scenarios of REQ-check-010, 011 and 012 as tests: ideas keep their verdict, outcome and links; a lesson's count
matches its occurrences and a repeated one is mechanized or waived; superseded ADRs name each other."""

import json
import subprocess
from pathlib import Path
from typing import Any

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


def of(out: dict[str, Any], check: str) -> list[dict[str, Any]]:
    return [finding for finding in out["findings"] if finding["check"] == check]


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def idea(
    number: str,
    status: str,
    verdict: str = "",
    change: str = "",
    prd: str = "",
    assessment: str = "",
    outcome: str = "",
) -> str:
    head = f"---\nid: {number}\ntitle: X\nstatus: {status}\nverdict: {verdict}\nsource: owner\ndate: 2026-11-21\n"
    head += (f"prd: {prd}\n" if prd else "") + (f"change: {change}\n" if change else "") + "---\n\n"
    return head + f"# {number} X\n\n## Proposal\n\nP.\n\n## Assessment\n\n{assessment}\n\n## Outcome\n\n{outcome}\n"


def change(change_id: str, status: str, decisions: str = "") -> str:
    return (
        f"---\nid: {change_id}\ntitle: T\npath: change\nstatus: {status}\napproved: 2026-11-21\n---\n\n# T\n\n"
        f"## Phases\n\n### 1. One\n\n- Role: developer\n- Depends on: —\n- Done when: it works\n\n"
        f"## Decisions\n\n{decisions}\n"
    )


def lesson(count: int, occurrences: list[str], status: str = "active", mechanism: str = "") -> str:
    items = "".join(f"- {item}\n" for item in occurrences)
    return (
        f"---\nid: L0003\ntitle: X\nstatus: {status}\ncount: {count}\nfirst: 2026-03-02\nlast: 2026-04-15\n"
        f"mechanism: {mechanism}\n---\n\n# L0003 X\n\n## Occurrences\n\n{items}\n## Gap\n\nG.\n\n## Rule\n\nR.\n"
    )


def adr(number: str, status: str = "accepted", supersedes: str = "", superseded_by: str = "") -> str:
    return (
        f"---\nid: {number}\ntitle: X\nstatus: {status}\ndate: 2026-11-21\ndecided-by: owner\n"
        f"supersedes: {supersedes}\nsuperseded-by: {superseded_by}\n---\n\n# {number} X\n"
    )


IDEA = "docs/product/ideas/I0004-x.md"
LESSON = "docs/lessons/L0003-x.md"


# REQ-check-010: ideas


def test_assessed_without_a_verdict(capsys, monkeypatch, project):
    write(project, IDEA, idea("I0004", "assessed", assessment="Value: some."))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert (finding["severity"], finding["file"], finding["line"]) == ("error", IDEA, 5)


def test_verdict_skipped_with_a_reason(capsys, monkeypatch, project):
    write(project, IDEA, idea("I0004", "planned", assessment="Skipped: the owner planned it straight away."))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "ideas") == []


def test_verdict_skipped_without_a_reason(capsys, monkeypatch, project):
    write(project, IDEA, idea("I0004", "planned"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert "empty Assessment" in finding["message"]


def test_declined_without_an_outcome(capsys, monkeypatch, project):
    write(project, IDEA, idea("I0004", "declined", verdict="stop", assessment="A."))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert "Outcome" in finding["message"]
    lines = (project / IDEA).read_text(encoding="utf-8").splitlines()
    assert finding["line"] == lines.index("## Outcome") + 1


def test_change_that_does_not_exist(capsys, monkeypatch, project):
    write(project, IDEA, idea("I0004", "planned", verdict="go", assessment="A.", change="C0042-x"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert "`C0042-x`" in finding["message"] and finding["line"] == 8


def test_change_is_not_checked_when_plans_are_in_another_repository(capsys, monkeypatch, project):
    write(project, ".keellay/config.toml", '[sections]\nchanges = "../other/changes"\n')
    write(project, IDEA, idea("I0004", "done", verdict="go", assessment="A.", change="C0042-x"))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "ideas") == []


def test_change_open_archived_or_only_deltas_exists(capsys, monkeypatch, project):
    write(project, "docs/changes/C0001-a/plan.md", change("C0001-a", "in-progress"))
    write(project, "docs/changes/archive/C0002-b/plan.md", change("C0002-b", "closed"))
    write(project, "docs/changes/C0003-c/delta/auth.md", "---\ncapability: auth\n---\n")
    for number, name in (("I0001", "C0001-a"), ("I0002", "C0002-b"), ("I0003", "C0003-c")):
        write(project, f"docs/product/ideas/{number}-x.md", idea(number, "planned", "go", name, assessment="A."))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "ideas") == []


def test_done_idea_whose_change_is_still_open(capsys, monkeypatch, project):
    write(project, "docs/changes/C0001-a/plan.md", change("C0001-a", "review"))
    write(project, IDEA, idea("I0004", "done", verdict="go", assessment="A.", change="C0001-a"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert "`C0001-a` is `review`, not `closed`" in finding["message"]


def test_done_idea_whose_change_closed(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0001-a/plan.md", change("C0001-a", "closed"))
    write(project, IDEA, idea("I0004", "done", verdict="go", assessment="A.", change="C0001-a"))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "ideas") == []


def test_unknown_prd_area(capsys, monkeypatch, project):
    write(
        project,
        "docs/product/prd.md",
        "---\nproduct: X\nupdated: 2026-11-21\n---\n\n# X\n\n## Areas\n\n"
        "### PRD-limits: Limits hold\n\n```markdown\n### PRD-export: example\n```\n",
    )
    write(project, IDEA, idea("I0004", "new", prd="PRD-export"))
    write(project, "docs/product/ideas/I0005-x.md", idea("I0005", "new", prd="PRD-limits"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "ideas")
    assert "`PRD-export`" in finding["message"] and finding["file"] == IDEA


# REQ-check-011: lessons


def test_count_and_occurrences_disagree(capsys, monkeypatch, project):
    write(project, LESSON, lesson(2, ["2026-03-02, C0001: a.", "2026-04-01, C0002: b.", "2026-04-15, C0003: c."]))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "lessons")
    assert finding["file"] == LESSON and "2" in finding["message"] and "3" in finding["message"]


def test_wrapped_and_nested_lines_are_one_occurrence(capsys, monkeypatch, project):
    write(project, LESSON, lesson(1, ["2026-03-02: a long one\n  that wraps\n  - with a nested note"]))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "lessons") == []


def test_repeated_lesson_closed_without_a_mechanism(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0007-x/plan.md", change("C0007-x", "closed", "1. Something else."))
    write(project, LESSON, lesson(2, ["2026-03-02, C0001: a.", "2026-04-15, C0007: b."]))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "lessons")
    assert finding["file"] == LESSON and "C0007" in finding["message"]
    assert "record the owner's waiver in those Decisions by naming L0003" in finding["message"]


def test_waived_mechanism(capsys, monkeypatch, project):
    write(
        project,
        "docs/changes/archive/C0007-x/plan.md",
        change("C0007-x", "closed", "1. L0003 gets a check of its own later (owner, waiver)."),
    )
    write(project, LESSON, lesson(2, ["2026-03-02, C0001: a.", "2026-04-15, C0007: b."]))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "lessons") == []


def test_repeated_lesson_whose_change_is_still_open(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-x/plan.md", change("C0007-x", "review"))
    write(project, LESSON, lesson(2, ["2026-03-02, C0001: a.", "2026-04-15, C0007: b."]))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "lessons") == []


def test_last_occurrence_outside_a_change_has_no_waiver_finding(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0001-x/plan.md", change("C0001-x", "closed"))
    write(project, LESSON, lesson(2, ["2026-03-02, C0001: a.", "2026-04-15, in a chat with the owner: b."]))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "lessons") == []


def test_mechanized_lesson_without_a_mechanism(capsys, monkeypatch, project):
    write(project, LESSON, lesson(1, ["2026-03-02: a."], status="mechanized"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "lessons")
    assert "`mechanism` is empty" in finding["message"] and finding["line"] == 8


def test_mechanized_lesson_with_a_mechanism(capsys, monkeypatch, project):
    write(
        project,
        LESSON,
        lesson(2, ["2026-03-02: a.", "2026-04-15: b."], status="mechanized", mechanism="backup check in CI"),
    )
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "lessons") == []


# REQ-check-012: superseded ADRs


def test_one_side_of_the_link_missing(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", adr("A0012", supersedes="A0004"))
    write(project, "docs/adr/A0004-x.md", adr("A0004", status="superseded"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "adr")
    assert finding["file"] == "docs/adr/A0004-x.md" and "A0012" in finding["message"]


def test_one_adr_supersedes_several(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", adr("A0012", supersedes="[A0004, A0007]"))
    write(project, "docs/adr/A0004-x.md", adr("A0004", status="superseded", superseded_by="A0012"))
    write(project, "docs/adr/A0007-x.md", adr("A0007", status="superseded", superseded_by="A0012"))
    _, out = run_check(project, capsys, monkeypatch)
    assert of(out, "adr") == []


def test_superseded_by_with_status_accepted(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", adr("A0012", supersedes="A0004"))
    write(project, "docs/adr/A0004-x.md", adr("A0004", superseded_by="A0012"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "adr")
    assert finding["file"] == "docs/adr/A0004-x.md" and "`accepted`" in finding["message"]


def test_superseded_by_names_an_adr_that_does_not_supersede_it(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", adr("A0012"))
    write(project, "docs/adr/A0004-x.md", adr("A0004", status="superseded", superseded_by="A0012"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "adr")
    assert finding["file"] == "docs/adr/A0012-x.md" and "A0004" in finding["message"]


def test_superseded_without_superseded_by(capsys, monkeypatch, project):
    write(project, "docs/adr/A0004-x.md", adr("A0004", status="superseded"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "adr")
    assert "`superseded-by`" in finding["message"]


@pytest.mark.parametrize(
    "status, supersedes, superseded_by",
    [
        ("superseded", "A0001", "A0001"),
        ("accepted", "A0001", ""),
    ],
)
def test_adr_that_supersedes_itself(capsys, monkeypatch, project, status, supersedes, superseded_by):
    write(project, "docs/adr/A0001-x.md", adr("A0001", status, supersedes, superseded_by))
    _, out = run_check(project, capsys, monkeypatch)
    findings = of(out, "adr")
    assert findings and all("A0001 itself" in finding["message"] for finding in findings)


def test_supersedes_an_adr_that_does_not_exist(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", adr("A0012", supersedes="A0004"))
    _, out = run_check(project, capsys, monkeypatch)
    [finding] = of(out, "adr")
    assert finding["file"] == "docs/adr/A0012-x.md" and "A0004" in finding["message"]

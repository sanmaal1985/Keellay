"""Scenarios of REQ-check-004 and REQ-check-005 as tests: unique numbers and the index of each section."""

import json
import subprocess
from pathlib import Path

import pytest

from conftest import add_constitution
from keellay.cli import main


def run_check(root: Path, capsys, monkeypatch):
    monkeypatch.chdir(root)
    code = main(["check"])
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


def plan(change_id: str, status: str = "in-progress") -> str:
    return f"---\nid: {change_id}\ntitle: T\npath: feature\nstatus: {status}\napproved: 2026-11-21\n---\n"


def idea(number: str, status: str) -> str:
    """An idea that is whole for its status, so that only the index is under test."""
    verdict = "" if status == "new" else "go"
    return (
        f"---\nid: {number}\ntitle: T\nstatus: {status}\nverdict: {verdict}\nsource: owner\ndate: 2026-11-21\n"
        f"change:\n---\n\n## Assessment\n\nA.\n\n## Outcome\n\nO.\n"
    )


def adr(number: str, status: str = "accepted", supersedes: str = "", superseded_by: str = "") -> str:
    return (
        f"---\nid: {number}\ntitle: T\nstatus: {status}\ndate: 2026-11-21\ndecided-by: owner\n"
        f"supersedes: {supersedes}\nsuperseded-by: {superseded_by}\n---\n"
    )


def lesson(number: str, status: str = "active") -> str:
    return (
        f"---\nid: {number}\ntitle: T\nstatus: {status}\ncount: 1\nfirst: 2026-11-21\nlast: 2026-11-21\n"
        f"mechanism:\n---\n"
    )


def spec(capability: str, prefix: str, *requirements: str) -> str:
    body = "".join(f"### {requirement}: Title\n\nThe CLI shall do it.\n\n" for requirement in requirements)
    return f"---\ncapability: {capability}\nprefix: {prefix}\n---\n\n# Spec\n\n## Requirements\n\n{body}"


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    add_constitution(tmp_path)
    return tmp_path


def findings_of(out: dict, check: str) -> list[dict]:
    return [finding for finding in out["findings"] if finding["check"] == check]


# REQ-check-004


def test_two_changes_with_one_number(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007-a/plan.md", plan("C0007-a"))
    write(project, "docs/changes/archive/C0007-b/plan.md", plan("C0007-b", "closed"))
    write(
        project,
        "docs/changes/README.md",
        "| ID | Title | Path | Status |\n|---|---|---|---|\n| [C0007](C0007-a/plan.md) | T | feature | in-progress |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = findings_of(out, "numbers")
    assert "C0007-a" in finding["file"] + finding["message"]
    assert "C0007-b" in finding["file"] + finding["message"]


def test_one_number_in_two_kinds_is_not_a_clash(capsys, monkeypatch, project):
    write(project, "docs/changes/C0006-a/plan.md", plan("C0006-a"))
    write(
        project,
        "docs/changes/README.md",
        "| ID | Title | Path | Status |\n|---|---|---|---|\n| [C0006](C0006-a/plan.md) | T | feature | in-progress |\n",
    )
    write(project, "docs/product/ideas/I0006-b.md", idea("I0006", "new"))
    write(
        project,
        "docs/product/README.md",
        "Ideas, open:\n\n| Idea | Title | Status |\n|---|---|---|\n| [I0006](ideas/I0006-b.md) | T | new |\n",
    )
    _, out = run_check(project, capsys, monkeypatch)
    assert findings_of(out, "numbers") == []


def test_change_folders_with_only_deltas_count_for_numbers(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0004-a/delta/check.md", "---\ncapability: check\n---\n")
    write(project, "docs/changes/archive/C0004-a/delta/cli.md", "---\ncapability: cli\n---\n")
    write(project, "docs/changes/archive/C0004-b/delta/paths.md", "---\ncapability: paths\n---\n")
    _, out = run_check(project, capsys, monkeypatch)
    (finding,) = findings_of(out, "numbers")
    assert "C0004-a" in finding["file"] + finding["message"] and "C0004-b" in finding["file"] + finding["message"]


@pytest.mark.parametrize(
    "folder, letter, make",
    [
        ("docs/product/ideas", "I", lambda n: idea(n, "new")),
        ("docs/adr", "A", lambda n: adr(n, "proposed")),
        ("docs/lessons", "L", lambda n: lesson(n, "retired")),
    ],
)
def test_two_files_with_one_number(capsys, monkeypatch, project, folder, letter, make):
    write(project, f"{folder}/{letter}0003-a.md", make(letter + "0003"))
    write(project, f"{folder}/{letter}0003-b.md", make(letter + "0003"))
    if folder.endswith("ideas"):
        write(
            project,
            "docs/product/README.md",
            "Ideas, open:\n\n| Idea | Title | Status |\n|---|---|---|\n"
            "| [I0003](ideas/I0003-a.md) | T | new |\n| [I0003](ideas/I0003-b.md) | T | new |\n",
        )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert len(findings_of(out, "numbers")) == 1


def test_requirement_id_used_twice(capsys, monkeypatch, project):
    write(project, "docs/specs/cli.md", spec("cli", "cli", "REQ-cli-001", "REQ-cli-002", "REQ-cli-001"))
    write(project, "docs/specs/README.md", "| Capability | Covers |\n|---|---|\n| [cli](cli.md) | CLI |\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = findings_of(out, "numbers")
    assert "REQ-cli-001" in finding["message"]


def test_requirement_id_with_another_prefix(capsys, monkeypatch, project):
    write(project, "docs/specs/cli.md", spec("cli", "cli", "REQ-cli-001", "REQ-auth-002"))
    write(project, "docs/specs/README.md", "| Capability | Covers |\n|---|---|\n| [cli](cli.md) | CLI |\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = findings_of(out, "numbers")
    assert "REQ-auth-002" in finding["message"]


# REQ-check-005


IDEAS_INDEX = (
    "# Product\n\nIdeas, open (in order of priority):\n\n"
    "| Idea | Title | Status | Verdict | Change |\n|---|---|---|---|---|\n{open}\n"
    "Ideas, closed:\n\n| Idea | Title | Status |\n|---|---|---|\n{closed}\n"
)


def test_ideas_in_the_right_tables_pass(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I0001-a.md", idea("I0001", "declined"))
    write(project, "docs/product/ideas/I0002-b.md", idea("I0002", "planned"))
    write(
        project,
        "docs/product/README.md",
        IDEAS_INDEX.format(
            open="| [I0002](ideas/I0002-b.md) | B | planned | | |",
            closed="| [I0001](ideas/I0001-a.md) | A | declined |",
        ),
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


def test_idea_in_the_wrong_table(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I0001-a.md", idea("I0001", "declined"))
    write(
        project,
        "docs/product/README.md",
        IDEAS_INDEX.format(open="| [I0001](ideas/I0001-a.md) | A | declined | | |", closed=""),
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = findings_of(out, "index")
    assert finding["file"] == "docs/product/README.md"
    assert "0001-a.md" in finding["message"]


def test_idea_not_listed(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I0001-a.md", idea("I0001", "new"))
    write(project, "docs/product/README.md", IDEAS_INDEX.format(open="", closed=""))
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "not listed" in findings_of(out, "index")[0]["message"]


def test_idea_listed_twice(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I0001-a.md", idea("I0001", "new"))
    row = "| [I0001](ideas/I0001-a.md) | A | new | | |"
    write(project, "docs/product/README.md", IDEAS_INDEX.format(open=f"{row}\n{row}", closed=""))
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "again" in findings_of(out, "index")[0]["message"]


def test_closed_change_still_listed(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0003-a/plan.md", plan("C0003-a", "closed"))
    write(
        project,
        "docs/changes/README.md",
        "| ID | Title | Path | Status |\n|---|---|---|---|\n| [C0003](C0003-a/plan.md) | A | feature | closed |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = findings_of(out, "index")
    assert finding["line"] == 3


def test_change_listed_with_another_status(capsys, monkeypatch, project):
    write(project, "docs/changes/C0004-a/plan.md", plan("C0004-a", "in-progress"))
    write(
        project,
        "docs/changes/README.md",
        "| ID | Title | Path | Status |\n|---|---|---|---|\n| [C0004](C0004-a/plan.md) | A | feature | review |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "review" in findings_of(out, "index")[0]["message"]


def test_open_change_without_an_index(capsys, monkeypatch, project):
    write(project, "docs/changes/C0004-a/plan.md", plan("C0004-a"))
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert findings_of(out, "index")[0]["file"] == "docs/changes/README.md"


def test_adr_index(capsys, monkeypatch, project):
    write(project, "docs/adr/A0001-a.md", adr("A0001", "superseded", superseded_by="A0002"))
    write(project, "docs/adr/A0002-b.md", adr("A0002", "accepted", supersedes="A0001"))
    write(project, "docs/adr/A0003-c.md", adr("A0003", "proposed"))
    write(
        project,
        "docs/adr/README.md",
        "# Decisions\n\nIn force:\n\n| ADR | Decision |\n|---|---|\n"
        "| [A0002](A0002-b.md) | B |\n\nReplaced:\n\n| ADR | Replaced by |\n|---|---|\n"
        "| [A0001](A0001-a.md) | A0002 |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


def test_superseded_adr_still_in_force(capsys, monkeypatch, project):
    write(project, "docs/adr/A0001-a.md", adr("A0001", "superseded"))
    write(
        project,
        "docs/adr/README.md",
        "# Decisions\n\nIn force:\n\n| ADR | Decision |\n|---|---|\n| [A0001](A0001-a.md) | A |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "In force" in findings_of(out, "index")[0]["message"]


def test_lesson_index(capsys, monkeypatch, project):
    write(project, "docs/lessons/L0001-a.md", lesson("L0001", "mechanized"))
    write(project, "docs/lessons/L0002-b.md", lesson("L0002", "active"))
    write(
        project,
        "docs/lessons/README.md",
        "# Lessons\n\nActive (read before working):\n\n"
        "| Lesson | Rule | Count |\n|---|---|---|\n| [L0001](L0001-a.md) | A | 1 |\n\n"
        "Mechanized:\n\n| Lesson | Mechanism |\n|---|---|\n| [L0002](L0002-b.md) | hook |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert len(findings_of(out, "index")) == 2


def test_spec_index(capsys, monkeypatch, project):
    write(project, "docs/specs/cli.md", spec("cli", "cli", "REQ-cli-001"))
    write(project, "docs/specs/paths.md", spec("paths", "paths", "REQ-paths-001"))
    write(
        project,
        "docs/specs/README.md",
        "| Capability | Covers |\n|---|---|\n| [cli](cli.md) | CLI |\n| [gone](gone.md) | Removed |\n",
    )
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    messages = [finding["message"] for finding in findings_of(out, "index")]
    assert any("paths.md" in message and "not listed" in message for message in messages)
    assert any("gone.md" in message for message in messages)


def test_tables_in_code_blocks_are_not_indexes(capsys, monkeypatch, project):
    write(project, "docs/specs/README.md", "```markdown\n| Capability | Covers |\n|---|---|\n| [x](x.md) | X |\n```\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])

"""Scenarios of REQ-check-003 as tests: one valid and one broken artifact per format, and the form of numbers."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import main

# Kind -> (path, valid front matter). Each is the format's own example, so a format change shows up here.
VALID = {
    "change": ("docs/changes/C0007-session-expiry/plan.md",
               "id: C0007-session-expiry\ntitle: Session expires\npath: feature\nstatus: in-progress\n"
               "approved: 2026-11-20\n"),
    "archived change": ("docs/changes/archive/C0006-export/plan.md",
                        "id: C0006-export\ntitle: Export\npath: change\nstatus: dropped\napproved:\n"),
    "idea": ("docs/product/ideas/I0004-shared-limits.md",
             "id: I0004\ntitle: Shared limits\nstatus: assessed\nverdict: clarify\nsource: owner\ndate: 2026-11-21\n"
             "prd: PRD-limits\nchange:\n"),
    "prd": ("docs/product/prd.md", "product: Family budget\nupdated: 2026-11-21\n"),
    "adr": ("docs/adr/A0012-expiry.md",
            "id: A0012\ntitle: Sessions expire\nstatus: accepted\ndate: 2026-11-20\ndecided-by: owner\n"
            "supersedes: [A0004, A0007]\nsuperseded-by:\n"),
    "lesson": ("docs/lessons/L0003-backup.md",
               "id: L0003\ntitle: No backup\nstatus: active\ncount: 2\nfirst: 2026-03-02\nlast: 2026-04-15\n"
               "mechanism:\n"),
    "spec": ("docs/specs/auth-session.md", "capability: auth-session\nprefix: auth\n"),
    "delta": ("docs/changes/C0007-session-expiry/delta/auth-session.md", "capability: auth-session\n"),
    "constitution": ("docs/constitution.md", "project: Family budget\nupdated: 2026-11-21\n"),
}

# Kind -> (front matter that breaks one rule, what the message names).
BROKEN = {
    "change": ("id: C0007-session-expiry\ntitle: Session expires\npath: epic\nstatus: in-progress\napproved:\n",
               "epic"),
    "archived change": ("id: C0006-export\ntitle: Export\npath: change\nstatus: finished\n", "finished"),
    "idea": ("id: I0004\ntitle: Shared limits\nstatus: started\nverdict:\nsource: owner\ndate: 2026-11-21\n"
             "change:\n", "started"),
    "prd": ("product: Family budget\nupdated: 21.11.2026\n", "21.11.2026"),
    "adr": ("id: A0012\ntitle: Sessions expire\nstatus: accepted\ndate: 2026-11-20\ndecided-by: owner\n"
            "supersedes: [4]\n", "supersedes"),
    "lesson": ("id: L0003\ntitle: No backup\nstatus: active\ncount: two\nfirst: 2026-03-02\nlast: 2026-04-15\n"
               "mechanism:\n", "two"),
    "spec": ("capability: auth-session\n", "prefix"),
    "delta": ("capability: auth\n", "auth-session"),
    "constitution": ("project:\nupdated: 2026-11-21\n", "project"),
}

ADR = "title: X\nstatus: proposed\ndate: 2026-11-21\ndecided-by: owner\n"


def run_check(root: Path, capsys, monkeypatch):
    """The exit code and the output, with only the front-matter findings: these files have no index around them."""
    monkeypatch.chdir(root)
    code = main(["check"])
    out = json.loads(capsys.readouterr().out)
    out["findings"] = [finding for finding in out["findings"] if finding["check"] == "front-matter"]
    if not out["findings"]:
        code = 0
    return code, out


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def project(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


@pytest.mark.parametrize("kind", sorted(VALID))
def test_valid_front_matter_passes(capsys, monkeypatch, project, kind):
    path, meta = VALID[kind]
    write(project, path, f"---\n{meta}---\n\n# Title\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("kind", sorted(BROKEN))
def test_broken_front_matter_is_reported(capsys, monkeypatch, project, kind):
    path, _ = VALID[kind]
    meta, named = BROKEN[kind]
    write(project, path, f"---\n{meta}---\n\n# Title\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert [(f["check"], f["file"]) for f in out["findings"]] == [("front-matter", path)]
    assert named in out["findings"][0]["message"]


def test_unknown_status_names_the_value_and_its_line(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I0004-x.md",
          "---\nid: I0004\ntitle: X\nstatus: started\nverdict:\nsource: owner\ndate: 2026-11-21\nchange:\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert "started" in finding["message"]
    assert finding["line"] == 4


def test_number_and_file_name_disagree(capsys, monkeypatch, project):
    write(project, "docs/lessons/L0003-x.md", "---\nid: L0004\ntitle: X\nstatus: active\ncount: 1\n"
          "first: 2026-11-21\nlast: 2026-11-21\nmechanism:\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert finding["file"] == "docs/lessons/L0003-x.md"
    assert "L0004" in finding["message"] and "L0003" in finding["message"]


def test_number_past_9999_passes(capsys, monkeypatch, project):
    write(project, "docs/product/ideas/I10000-x.md",
          "---\nid: I10000\ntitle: X\nstatus: new\nsource: owner\ndate: 2026-11-21\n---\n")
    write(project, "docs/changes/C10000-x/plan.md", "---\nid: C10000-x\ntitle: X\npath: change\nstatus: draft\n---\n")
    write(project, "docs/adr/A10000-x.md", f"---\nid: A10000\n{ADR}supersedes: [A0012, A10001]\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


def test_numbers_keep_their_leading_zeros(capsys, monkeypatch, project):
    write(project, "docs/adr/A0012-x.md", f"---\nid: A0012\n{ADR}---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


def test_bare_number_names_the_expected_form(capsys, monkeypatch, project):
    write(project, "docs/adr/0012-x.md", f"---\nid: 0012\n{ADR}---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert {f["file"] for f in out["findings"]} == {"docs/adr/0012-x.md"}
    assert all("A0012" in f["message"] for f in out["findings"])


def test_another_kinds_letter_is_reported(capsys, monkeypatch, project):
    write(project, "docs/adr/A0013-x.md", f"---\nid: A0013\n{ADR}supersedes: C0004\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert "supersedes" in finding["message"] and "A0004" in finding["message"]


@pytest.mark.parametrize("path, meta, expected", [
    ("docs/lessons/A0003-x.md", "id: A0003\ntitle: X\nstatus: active\ncount: 1\nfirst: 2026-11-21\n"
     "last: 2026-11-21\n", "L0003"),
    ("docs/changes/0007-x/plan.md", "id: 0007-x\ntitle: X\npath: change\nstatus: draft\n", "C0007"),
    ("docs/product/ideas/I0004-x.md", "id: I0004\ntitle: X\nstatus: planned\nsource: owner\ndate: 2026-11-21\n"
     "change: 0007-x\n", "C0007"),
])
def test_wrong_or_missing_letter_in_names_and_fields(capsys, monkeypatch, project, path, meta, expected):
    write(project, path, f"---\n{meta}---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert any(expected in f["message"] for f in out["findings"])


@pytest.mark.parametrize("path, meta", [
    ("docs/adr/A00012-x.md", "id: A00012\n" + ADR),
    ("docs/adr/A0013-x.md", "id: A0013\n" + ADR + "supersedes: A00012\n"),
    ("docs/product/ideas/I0004-x.md", "id: I0004\ntitle: X\nstatus: planned\nsource: owner\ndate: 2026-11-21\n"
     "change: C00007-x\n"),
])
def test_a_padding_zero_past_four_digits_is_reported(capsys, monkeypatch, project, path, meta):
    write(project, path, f"---\n{meta}---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert any("0012" in f["message"] or "C0007" in f["message"] for f in out["findings"])


def test_change_folder_without_a_topic_is_told_the_change_id(capsys, monkeypatch, project):
    write(project, "docs/changes/C0007/plan.md", "---\nid: C0007\ntitle: X\npath: change\nstatus: draft\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert any("must be the change ID, as `C0007-topic`" in f["message"] for f in out["findings"])


@pytest.mark.parametrize("folder", ["docs/changes/0004-checks", "docs/changes/archive/0004-checks"])
def test_change_folder_with_only_deltas_carries_the_change_id(capsys, monkeypatch, project, folder):
    write(project, f"{folder}/delta/check.md", "---\ncapability: check\n---\n")
    write(project, f"{folder}/delta/cli.md", "---\ncapability: cli\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert "C0004-topic" in finding["message"]


def test_change_folder_with_only_deltas_in_the_new_form_passes(capsys, monkeypatch, project):
    write(project, "docs/changes/archive/C0004-checks/delta/check.md", "---\ncapability: check\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("text, named", [
    ("# No front matter\n", "no front matter"),
    ("---\nid: A0012\n", "not closed"),
    ("---\nid: [A0012\n---\n", "not valid YAML"),
    ("---\n- id\n---\n", "mapping"),
])
def test_unreadable_front_matter(capsys, monkeypatch, project, text, named):
    write(project, "docs/adr/A0012-x.md", text)
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert finding["check"] == "front-matter"
    assert named in finding["message"]


def test_file_name_without_a_number(capsys, monkeypatch, project):
    write(project, "docs/adr/expiry.md", f"---\nid: A0012\n{ADR}---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "A0007-topic.md" in out["findings"][0]["message"]


def test_indexes_and_other_files_are_not_artifacts(capsys, monkeypatch, project):
    write(project, "docs/adr/README.md", "# Decisions\n")
    write(project, "docs/changes/README.md", "# Changes\n")
    write(project, "docs/changes/C0007-x/design.md", "# Design notes, no front matter\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])

"""Scenarios of REQ-check-003 (change 0004) as tests: one valid and one broken artifact per format."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import main

# Kind -> (path, valid front matter). Each is the format's own example, so a format change shows up here.
VALID = {
    "change": ("docs/changes/0007-session-expiry/plan.md",
               "id: 0007-session-expiry\ntitle: Session expires\npath: feature\nstatus: in-progress\n"
               "approved: 2026-11-20\n"),
    "archived change": ("docs/changes/archive/0006-export/plan.md",
                        "id: 0006-export\ntitle: Export\npath: change\nstatus: dropped\napproved:\n"),
    "idea": ("docs/product/ideas/0004-shared-limits.md",
             "id: 0004\ntitle: Shared limits\nstatus: assessed\nverdict: clarify\nsource: owner\ndate: 2026-11-21\n"
             "prd: PRD-limits\nchange:\n"),
    "prd": ("docs/product/prd.md", "product: Family budget\nupdated: 2026-11-21\n"),
    "adr": ("docs/adr/0012-expiry.md",
            "id: 0012\ntitle: Sessions expire\nstatus: accepted\ndate: 2026-11-20\ndecided-by: owner\n"
            "supersedes: [0004, 0007]\nsuperseded-by:\n"),
    "lesson": ("docs/lessons/0003-backup.md",
               "id: 0003\ntitle: No backup\nstatus: active\ncount: 2\nfirst: 2026-03-02\nlast: 2026-04-15\n"
               "mechanism:\n"),
    "spec": ("docs/specs/auth-session.md", "capability: auth-session\nprefix: auth\n"),
    "delta": ("docs/changes/0007-session-expiry/delta/auth-session.md", "capability: auth-session\n"),
    "constitution": ("docs/constitution.md", "project: Family budget\nupdated: 2026-11-21\n"),
}

# Kind -> (front matter that breaks one rule, what the message names).
BROKEN = {
    "change": ("id: 0007-session-expiry\ntitle: Session expires\npath: epic\nstatus: in-progress\napproved:\n",
               "epic"),
    "archived change": ("id: 0006-export\ntitle: Export\npath: change\nstatus: dropped\n", "approved"),
    "idea": ("id: 0004\ntitle: Shared limits\nstatus: started\nverdict:\nsource: owner\ndate: 2026-11-21\n"
             "change:\n", "started"),
    "prd": ("product: Family budget\nupdated: 21.11.2026\n", "21.11.2026"),
    "adr": ("id: 0012\ntitle: Sessions expire\nstatus: accepted\ndate: 2026-11-20\ndecided-by: owner\n"
            "supersedes: [4]\n", "supersedes"),
    "lesson": ("id: 0003\ntitle: No backup\nstatus: active\ncount: two\nfirst: 2026-03-02\nlast: 2026-04-15\n"
               "mechanism:\n", "two"),
    "spec": ("capability: auth-session\n", "prefix"),
    "delta": ("capability: auth\n", "auth-session"),
    "constitution": ("project:\nupdated: 2026-11-21\n", "project"),
}


def run_check(root: Path, capsys, monkeypatch):
    monkeypatch.chdir(root)
    code = main(["check"])
    return code, json.loads(capsys.readouterr().out)


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
    write(project, "docs/product/ideas/0004-x.md",
          "---\nid: 0004\ntitle: X\nstatus: started\nverdict:\nsource: owner\ndate: 2026-11-21\nchange:\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert "started" in finding["message"]
    assert finding["line"] == 4


def test_number_and_file_name_disagree(capsys, monkeypatch, project):
    write(project, "docs/lessons/0003-x.md", "---\nid: 0004\ntitle: X\nstatus: active\ncount: 1\n"
          "first: 2026-11-21\nlast: 2026-11-21\nmechanism:\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert finding["file"] == "docs/lessons/0003-x.md"
    assert "0004" in finding["message"] and "0003" in finding["message"]


def test_numbers_keep_their_leading_zeros(capsys, monkeypatch, project):
    write(project, "docs/adr/0012-x.md", "---\nid: 0012\ntitle: X\nstatus: proposed\ndate: 2026-11-21\n"
          "decided-by: owner\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("text, named", [
    ("# No front matter\n", "no front matter"),
    ("---\nid: 0012\n", "not closed"),
    ("---\nid: [0012\n---\n", "not valid YAML"),
    ("---\n- id\n---\n", "mapping"),
])
def test_unreadable_front_matter(capsys, monkeypatch, project, text, named):
    write(project, "docs/adr/0012-x.md", text)
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    (finding,) = out["findings"]
    assert finding["check"] == "front-matter"
    assert named in finding["message"]


def test_file_name_without_a_number(capsys, monkeypatch, project):
    write(project, "docs/adr/expiry.md", "---\nid: 0012\ntitle: X\nstatus: proposed\ndate: 2026-11-21\n"
          "decided-by: owner\n---\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert code == 1
    assert "four-digit number" in out["findings"][0]["message"]


def test_indexes_and_other_files_are_not_artifacts(capsys, monkeypatch, project):
    write(project, "docs/adr/README.md", "# Decisions\n")
    write(project, "docs/changes/README.md", "# Changes\n")
    write(project, "docs/changes/0007-x/design.md", "# Design notes, no front matter\n")
    code, out = run_check(project, capsys, monkeypatch)
    assert (code, out["findings"]) == (0, [])

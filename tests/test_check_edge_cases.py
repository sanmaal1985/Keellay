"""Cases found by the fresh-context review of change 0004: encodings, odd paths, crashes and code examples."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import main

ADR = "---\nid: 0001\ntitle: X\nstatus: accepted\ndate: 2026-11-21\ndecided-by: owner\n---\n\n# 0001\n"
ADR_INDEX = "# Decisions\n\nIn force:\n\n| ADR | Decision |\n|---|---|\n| [0001](0001-x.md) | X |\n"


def run(capsys, *argv):
    code = main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, path: str, text: str, encoding: str = "utf-8") -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.encode(encoding))


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def project(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_project_in_a_folder_with_a_non_ascii_name(capsys, tmp_path, monkeypatch):
    root = tmp_path / "проект"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    write(root, "docs/adr/0001-x.md", ADR.replace("accepted", "started"))
    write(root, "docs/adr/README.md", ADR_INDEX)
    monkeypatch.chdir(root)
    code, out = run(capsys, "check")
    assert code == 1
    assert any(f["check"] == "front-matter" and "started" in f["message"] for f in out["findings"])
    code, out = run(capsys, "check", "--staged")
    assert out["status"] == "ok"  # nothing staged yet: the index is read, not a wrong folder


def test_byte_order_mark_is_not_a_missing_front_matter(capsys, project):
    write(project, "docs/adr/0001-x.md", "﻿" + ADR)
    write(project, "docs/adr/README.md", ADR_INDEX)
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("staged", [False, True])
def test_file_that_is_not_utf8_is_read_not_a_crash(capsys, project, staged):
    write(project, "docs/adr/0001-x.md", ADR)
    write(project, "docs/adr/README.md", ADR_INDEX + "\nРешения: [нет](missing.md)\n", encoding="cp1251")
    git(project, "add", "-A")
    code, out = run(capsys, "check", *(["--staged"] if staged else []))
    assert code == 1
    assert [f["check"] for f in out["findings"]] == ["links"]


def test_status_that_is_a_list_is_a_finding_not_a_crash(capsys, project):
    write(project, "docs/adr/0001-x.md", ADR.replace("status: accepted", "status: [accepted]"))
    write(project, "docs/adr/README.md", ADR_INDEX)
    code, out = run(capsys, "check")
    assert code == 1
    assert "front-matter" in {f["check"] for f in out["findings"]}


def test_non_ascii_file_names_give_ascii_json(capsys, project):
    write(project, "docs/adr/README.md", "[日本](日本.md)\n")
    code = main(["check"])
    raw = capsys.readouterr().out
    assert raw.isascii()
    assert json.loads(raw)["findings"][0]["message"] == "link to 日本.md points to nothing"
    assert code == 1


def test_staged_with_a_merge_conflict_is_not_a_crash(capsys, project):
    git(project, "config", "user.email", "test@example.com")
    git(project, "config", "user.name", "Test")
    write(project, "docs/adr/README.md", "# Decisions\n")
    git(project, "add", "-A")
    git(project, "commit", "-q", "-m", "base")
    git(project, "checkout", "-q", "-b", "other")
    write(project, "docs/adr/README.md", "# Decisions, other\n")
    git(project, "commit", "-q", "-am", "other")
    git(project, "checkout", "-q", "-")
    write(project, "docs/adr/README.md", "# Decisions, main\n")
    git(project, "commit", "-q", "-am", "main")
    subprocess.run(["git", "merge", "-q", "other"], cwd=project, capture_output=True)
    code, out = run(capsys, "check", "--staged")
    assert out["command"] == "check"
    assert out["status"] in ("ok", "failed")


def test_link_text_wrapped_onto_the_next_line(capsys, project):
    write(project, "docs/adr/README.md", "See the [missing\nfile](missing.md) here.\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert [(f["check"], f["line"]) for f in out["findings"]] == [("links", 2)]


def test_image_inside_a_link(capsys, project):
    write(project, "docs/adr/README.md", "[![build](missing.png)](https://example.com/ci)\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert "missing.png" in out["findings"][0]["message"]


def test_requirement_headings_in_code_blocks_are_examples(capsys, project):
    write(project, "docs/specs/merge.md", "---\ncapability: merge\nprefix: merge\n---\n\n# Merge\n\n"
          "## Requirements\n\n### REQ-merge-001: Merge\n\nThe CLI shall merge.\n\n"
          "```markdown\n### REQ-auth-003: Example\n### REQ-merge-001: Example\n```\n")
    write(project, "docs/specs/README.md", "| Capability | Covers |\n|---|---|\n| [merge](merge.md) | Merge |\n")
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


def test_build_and_dist_folders_are_project_files(capsys, project):
    write(project, "build/guide.md", "# Guide\n")
    write(project, "dist/notes.md", "# Notes\n")
    write(project, "docs/adr/README.md", "[guide](../../build/guide.md), [notes](../../dist/notes.md)\n")
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("text", [
    "[Owner, 2026-11-21]:\nall options as recommended.\n",
    "[label]: missing.md and more words\n",
    "Items [a\n\nb](missing.md)\n",
])
def test_text_that_only_looks_like_a_link(capsys, project, text):
    write(project, "docs/adr/README.md", text)
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


def test_reference_definition_with_a_title_is_checked(capsys, project):
    write(project, "docs/adr/README.md", '[label]: missing.md "Title"\n')
    code, out = run(capsys, "check")
    assert code == 1


def test_extra_link_path_with_a_leading_slash_names_a_file(capsys, project):
    write(project, ".keellay/config.toml", '[check]\nlinks = ["/README.md"]\n')
    write(project, "README.md", "[x](missing.md)\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert out["findings"][0]["file"] == "README.md"


@pytest.mark.parametrize("links", ['["./method"]', '["method/"]', '["method\\\\"]', '["/method"]'])
def test_extra_link_paths_are_normalized(capsys, project, links):
    write(project, ".keellay/config.toml", f"[check]\nlinks = {links}\n")
    write(project, "method/a.md", "[missing](missing.md)\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert out["findings"][0]["file"] == "method/a.md"


def test_section_at_the_root(capsys, project):
    write(project, ".keellay/config.toml", '[sections]\nspecs = "."\n')
    write(project, "auth.md", "---\ncapability: session\nprefix: auth\n---\n")
    write(project, "README.md", "| Capability | Covers |\n|---|---|\n| [auth](auth.md) | Auth |\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert [(f["check"], f["file"]) for f in out["findings"]] == [("front-matter", "auth.md")]


def test_staged_reads_the_staged_config(capsys, project):
    write(project, "decisions/README.md", "[missing](0009-x.md)\n")
    git(project, "add", "-A")
    # Not staged: a config that would make `decisions` a section, so its broken link would be read.
    write(project, ".keellay/config.toml", '[sections]\nadr = "decisions"\n')
    code, out = run(capsys, "check", "--staged")
    assert (code, out["findings"]) == (0, [])
    code, out = run(capsys, "check")
    assert code == 1


@pytest.mark.parametrize("path, meta", [
    ("docs/product/ideas/0001-x.md", "id: 0001\ntitle: X\nstatus: new\nsource: owner\ndate: 2026-11-21\n"),
    ("docs/lessons/0001-x.md", "id: 0001\ntitle: X\nstatus: active\ncount: 1\nfirst: 2026-11-21\nlast: 2026-11-21\n"),
    ("docs/changes/0001-x/plan.md", "id: 0001-x\ntitle: X\npath: change\nstatus: draft\n"),
])
def test_fields_set_later_may_be_left_out(capsys, project, path, meta):
    write(project, path, f"---\n{meta}---\n")
    code, out = run(capsys, "check")
    assert [f for f in out["findings"] if f["check"] == "front-matter"] == []

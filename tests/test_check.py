"""Scenarios of the `check` delta (change 0004) as tests: the command, the `links` check and `--staged`."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import EXIT_CONFIG_ERROR, EXIT_FINDINGS, main


def run(capsys, *argv):
    code = main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def write(root: Path, path: str, text: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def project(tmp_path, monkeypatch):
    """An empty git repository as the current folder."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def git_add(root: Path, *paths: str) -> None:
    subprocess.run(["git", "add", *paths], cwd=root, check=True)


# REQ-check-001


def test_clean_project_reports_ok(capsys, project):
    write(project, "AGENTS.md", "Read [the constitution](docs/constitution.md).\n")
    write(project, "docs/constitution.md", "# Constitution\n\nDecisions: [adr](adr/).\n")
    (project / "docs" / "adr").mkdir()
    write(project, "docs/adr/README.md", "# Decisions\n")
    code, out = run(capsys, "check")
    assert code == 0
    assert out == {"command": "check", "status": "ok", "findings": []}


# REQ-check-002


def test_broken_link_is_reported_as_an_error(capsys, project):
    write(project, "docs/adr/README.md", "# Decisions\n\n- [0009](0009-missing.md)\n")
    code, out = run(capsys, "check")
    assert code == EXIT_FINDINGS == 1
    assert out["status"] == "failed"
    assert out["findings"] == [{"check": "links", "severity": "error", "file": "docs/adr/README.md", "line": 3,
                                "message": "link to 0009-missing.md points to nothing"}]


# REQ-check-006


@pytest.mark.parametrize("text", [
    "```markdown\n[plan](0007-x/plan.md)\n```\n",
    "~~~\n[plan](0007-x/plan.md)\n~~~\n",
    "  ```\n  [plan](0007-x/plan.md)\n  ```\n",
    "See `[plan](0007-x/plan.md)` in the format.\n",
    "[site](https://example.com/missing) and [mail](mailto:someone@example.com)\n",
    "[here](#requirements)\n",
    "[outside](../../../other-repo/file.md)\n",
])
def test_links_that_are_not_checked(capsys, project, text):
    write(project, "docs/changes/README.md", text)
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


@pytest.mark.parametrize("text", [
    "[plan](0007-x/plan.md)\n",
    "![diagram](img/flow.png)\n",
    "[plan](<0007 x/plan.md>)\n",
    "[plan](0007-x/plan.md \"title\")\n",
    "[plan]: 0007-x/plan.md\n",
    "```\n[ok](README.md)\n```\n[plan](0007-x/plan.md)\n",
])
def test_links_that_are_checked(capsys, project, text):
    write(project, "docs/changes/README.md", text)
    code, out = run(capsys, "check")
    assert code == 1
    assert [finding["check"] for finding in out["findings"]] == ["links"]


def test_anchor_and_folder_targets_resolve(capsys, project):
    write(project, "docs/adr/0001-x.md", "# 0001\n")
    write(project, "docs/changes/README.md", "[adr](../adr/0001-x.md#context), [folder](../adr/), [up](../adr)\n")
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


def test_extra_paths_from_the_config(capsys, project):
    write(project, ".keellay/config.toml", '[check]\nlinks = ["method", "README.md"]\n')
    write(project, "method/formats/adr.md", "See [missing](missing.md).\n")
    write(project, "README.md", "See [method](method/formats/adr.md).\n")
    code, out = run(capsys, "check")
    assert code == 1
    assert [(f["check"], f["file"]) for f in out["findings"]] == [("links", "method/formats/adr.md")]


def test_files_outside_sections_and_extra_paths_are_not_read(capsys, project):
    write(project, "notes/todo.md", "[missing](missing.md)\n")
    code, out = run(capsys, "check")
    assert (code, out["findings"]) == (0, [])


def test_a_section_mapped_elsewhere_is_read_there(capsys, project):
    write(project, ".keellay/config.toml", '[sections]\nadr = "decisions"\n')
    write(project, "decisions/README.md", "[missing](0001-x.md)\n")
    code, out = run(capsys, "check")
    assert [f["file"] for f in out["findings"]] == ["decisions/README.md"]


# REQ-check-007


def test_staged_ignores_an_unstaged_broken_file(capsys, project):
    write(project, "docs/adr/README.md", "# Decisions\n\n- [0001](0001-x.md)\n")
    write(project, "docs/adr/0001-x.md", "# 0001\n")
    git_add(project, "docs/adr/README.md", "docs/adr/0001-x.md")
    write(project, "docs/lessons/README.md", "[missing](0009-x.md)\n")
    code, out = run(capsys, "check", "--staged")
    assert (code, out["status"]) == (0, "ok")


def test_staged_reads_the_staged_content_not_the_working_tree(capsys, project):
    write(project, "docs/adr/README.md", "[missing](0009-x.md)\n")
    git_add(project, "docs/adr/README.md")
    write(project, "docs/adr/README.md", "# fixed in the working tree, not staged\n")
    code, out = run(capsys, "check", "--staged")
    assert code == 1
    assert out["findings"][0]["file"] == "docs/adr/README.md"


def test_staged_treats_unstaged_files_as_absent(capsys, project):
    write(project, "docs/adr/README.md", "[0001](0001-x.md)\n")
    git_add(project, "docs/adr/README.md")
    write(project, "docs/adr/0001-x.md", "# 0001, not staged\n")
    code, out = run(capsys, "check", "--staged")
    assert code == 1


def test_staged_outside_git_is_an_error(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    code, out = run(capsys, "check", "--staged")
    assert code == EXIT_CONFIG_ERROR
    assert out["status"] == "error"


# REQ-check-008


@pytest.mark.parametrize("config, named", [
    ('[sections]\ntasks = "docs/tasks"\n', "tasks"),
    ('level = "medium"\n', "medium"),
    ('[check]\nlinks = "method"\n', "links"),
    ('[check]\nlinks = [1]\n', "links"),
])
def test_invalid_config(capsys, project, config, named):
    write(project, ".keellay/config.toml", config)
    code, out = run(capsys, "check")
    assert code == EXIT_CONFIG_ERROR == 2
    assert out["command"] == "check"
    assert out["status"] == "error"
    assert named in out["message"]
    assert "findings" not in out

"""Scenarios of the `paths` delta (change 0004) as tests."""

import json
import subprocess
from pathlib import Path

import pytest

from keellay.cli import EXIT_CONFIG_ERROR, main
from keellay.method_files import method_dir
from keellay.paths import DEFAULT_SECTIONS


def run(capsys, *argv):
    code = main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def write_config(root: Path, text: str) -> None:
    (root / ".keellay").mkdir(exist_ok=True)
    (root / ".keellay" / "config.toml").write_text(text, encoding="utf-8")


def test_root_is_the_git_top_level_from_a_subfolder(capsys, tmp_path, monkeypatch):
    git_init(tmp_path)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    monkeypatch.chdir(tmp_path / "docs" / "adr")
    code, out = run(capsys, "paths")
    assert code == 0
    assert Path(out["root"]) == tmp_path.resolve()


def test_root_is_the_current_folder_outside_git(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    code, out = run(capsys, "paths")
    assert code == 0
    assert Path(out["root"]) == tmp_path.resolve()


def test_defaults_without_a_config(capsys, tmp_path, monkeypatch):
    git_init(tmp_path)
    (tmp_path / "docs" / "adr").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    code, out = run(capsys, "paths")
    assert code == 0
    assert out["command"] == "paths"
    assert out["status"] == "ok"
    assert out["level"] == "standard"
    assert out["sections"]["adr"] == {"path": "docs/adr", "exists": True}
    assert out["sections"]["lessons"] == {"path": "docs/lessons", "exists": False}
    assert set(out["sections"]) == set(DEFAULT_SECTIONS)


def test_defaults_match_the_layout_in_the_method():
    layout = (method_dir()[0] / "layout.md").read_text(encoding="utf-8")
    for path in DEFAULT_SECTIONS.values():
        assert Path(path).name in layout, path


def test_config_overrides_level_and_sections(capsys, tmp_path, monkeypatch):
    git_init(tmp_path)
    write_config(tmp_path, 'level = "light"\n\n[sections]\nspecs = "../other/docs/specs"\nlessons = false\n')
    monkeypatch.chdir(tmp_path)
    code, out = run(capsys, "paths")
    assert code == 0
    assert out["level"] == "light"
    assert out["sections"]["specs"]["path"] == "../other/docs/specs"
    assert out["sections"]["lessons"] == {"path": None, "exists": False}


@pytest.mark.parametrize("config, named", [
    ('level = "medium"\n', "medium"),
    ('[sections]\ntasks = "docs/tasks"\n', "tasks"),
    ('[sections]\nadr = 3\n', "adr"),
    ('[sections]\nadr = true\n', "adr"),
    ('level = \n', "TOML"),
])
def test_invalid_config(capsys, tmp_path, monkeypatch, config, named):
    git_init(tmp_path)
    write_config(tmp_path, config)
    monkeypatch.chdir(tmp_path)
    code, out = run(capsys, "paths")
    assert code == EXIT_CONFIG_ERROR == 2
    assert out["command"] == "paths"
    assert out["status"] == "error"
    assert named in out["message"]

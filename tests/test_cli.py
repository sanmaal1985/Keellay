import json
from pathlib import Path

import pytest

from keellay import __version__
from keellay.cli import EXIT_NOT_IMPLEMENTED, PLANNED, main


def run(capsys, *argv):
    code = main(list(argv))
    return code, json.loads(capsys.readouterr().out)


def test_version(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"keellay {__version__}"


def test_info_finds_the_method(capsys):
    code, out = run(capsys, "info")
    assert code == 0
    assert out["status"] == "ok"
    assert out["version"] == __version__
    assert Path(out["method_dir"], "README.md").is_file()


@pytest.mark.parametrize("command", sorted(PLANNED))
def test_planned_commands_report_not_implemented(capsys, command):
    code, out = run(capsys, command)
    assert code == EXIT_NOT_IMPLEMENTED
    assert out == {"command": command, "status": "not_implemented", "message": PLANNED[command]}

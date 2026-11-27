"""Helpers shared by the test files."""

import subprocess
from pathlib import Path

CONSTITUTION = (
    "---\nproject: Test\nupdated: 2026-11-21\n---\n\n# Constitution: Test\n\n## Project\n\nA test project.\n\n"
    "## Owner\n\nThe owner decides.\n\n## Read first\n\n1. Nothing yet.\n\n## Rules\n\n- Check before "
    "claiming.\n"
)


def add_constitution(root: Path, path: str = "docs/constitution.md") -> None:
    """Give a test project the constitution and the `AGENTS.md` line every project has, staged as well, so that a
    test of another check sees no `constitution` finding, also with `--staged`."""
    for name, text in ((path, CONSTITUTION), ("AGENTS.md", f"Before any work, read [{path}]({path}) and follow it.\n")):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    if (root / ".git").exists():
        subprocess.run(["git", "add", path, "AGENTS.md"], cwd=root, check=True, capture_output=True)

"""Resolve a project's root, level and artifact sections: the one resolver that checks and other commands use.

Defaults follow `method/layout.md`; a project overrides them in `.keellay/config.toml`.
"""

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILE = Path(".keellay") / "config.toml"

LEVELS = ("light", "standard", "strict")
DEFAULT_LEVEL = "standard"

# Section name -> default path relative to the root, as in `method/layout.md` (a test keeps the two in step).
DEFAULT_SECTIONS = {
    "constitution": "docs/constitution.md",
    "product": "docs/product",
    "specs": "docs/specs",
    "changes": "docs/changes",
    "adr": "docs/adr",
    "lessons": "docs/lessons",
}


class ConfigError(Exception):
    """The project's config cannot be used; the message names the problem."""


@dataclass(frozen=True)
class Section:
    path: str | None  # relative to the root, with `/`; None when the project has no such section

    def resolve(self, root: Path) -> Path | None:
        return None if self.path is None else root / self.path


@dataclass(frozen=True)
class Project:
    root: Path
    level: str
    sections: dict[str, Section]
    config: dict

    def section_dir(self, name: str) -> Path | None:
        """The section's path when it exists, else None: checks skip a section that is not there."""
        path = self.sections[name].resolve(self.root)
        return path if path is not None and path.exists() else None


def find_root(cwd: Path | None = None) -> Path:
    """The git repository's top-level folder, or the current folder outside git."""
    cwd = Path.cwd() if cwd is None else cwd
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True, text=True,
                                check=False)
    except OSError:
        return cwd.resolve()
    if result.returncode != 0 or not result.stdout.strip():
        return cwd.resolve()
    return Path(result.stdout.strip()).resolve()


def load_project(root: Path | None = None) -> Project:
    root = find_root() if root is None else root
    config = _read_config(root)

    level = config.get("level", DEFAULT_LEVEL)
    if level not in LEVELS:
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: unknown level {level!r}; expected one of {', '.join(LEVELS)}")

    mapped = config.get("sections", {})
    if not isinstance(mapped, dict):
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: [sections] must be a table")
    sections = {name: Section(path) for name, path in DEFAULT_SECTIONS.items()}
    for name, value in mapped.items():
        if name not in DEFAULT_SECTIONS:
            raise ConfigError(f"{CONFIG_FILE.as_posix()}: unknown section {name!r}; expected one of "
                              f"{', '.join(DEFAULT_SECTIONS)}")
        if value is False:
            sections[name] = Section(None)
        elif isinstance(value, str) and value.strip():
            sections[name] = Section(value.replace("\\", "/"))
        else:
            raise ConfigError(f"{CONFIG_FILE.as_posix()}: section {name!r} must be a path or false, not {value!r}")
    return Project(root=root, level=level, sections=sections, config=config)


def _read_config(root: Path) -> dict:
    path = root / CONFIG_FILE
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as file:
            return tomllib.load(file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: not valid TOML: {error}") from error

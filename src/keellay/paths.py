"""Resolve a project's root, level and artifact sections: the one resolver that checks and other commands use.

Defaults follow `method/layout.md`; a project overrides them in `.keellay/config.toml`.
"""

import posixpath
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


def find_root(cwd: Path | None = None) -> Path:
    """The git repository's top-level folder, or the current folder outside git."""
    cwd = Path.cwd() if cwd is None else cwd
    try:
        # Git prints the path in UTF-8 whatever the system code page is, so a folder named in Cyrillic stays intact.
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd, capture_output=True,
                                encoding="utf-8", errors="replace", check=False)
    except OSError:
        return cwd.resolve()
    if result.returncode != 0 or not result.stdout.strip():
        return cwd.resolve()
    return Path(result.stdout.strip()).resolve()


def load_project(root: Path | None = None, config_text: str | None = None, config_given: bool = False) -> Project:
    """The project at the root. With `config_given`, the config is `config_text` (None: no config) instead of the
    file on disk, so `check --staged` reads the config that is staged."""
    root = find_root() if root is None else root
    config = _parse_config(config_text) if config_given else _read_config(root)

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
            sections[name] = Section(posixpath.normpath(value.strip().replace("\\", "/")))
        else:
            raise ConfigError(f"{CONFIG_FILE.as_posix()}: section {name!r} must be a path or false, not {value!r}")
    return Project(root=root, level=level, sections=sections, config=config)


def _read_config(root: Path) -> dict:
    path = root / CONFIG_FILE
    if not path.is_file():
        return {}
    return _parse_config(path.read_bytes().decode("utf-8-sig", errors="replace"))


def _parse_config(text: str | None) -> dict:
    if text is None:
        return {}
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: not valid TOML: {error}") from error

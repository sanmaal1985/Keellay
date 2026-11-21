"""Project checks run by `keellay check` from git hooks and CI; agent hooks call the same command.

Each check reads the project through a `Source`, so the same code checks the working tree or the files staged for a
commit, and returns findings; the command reports them as one JSON object.
"""

import posixpath
from dataclasses import asdict, dataclass

from keellay.checks.source import Source
from keellay.paths import CONFIG_FILE, ConfigError, Project

SEVERITIES = ("error", "warning", "advice")


@dataclass(frozen=True)
class Finding:
    check: str
    severity: str
    file: str
    line: int | None
    message: str

    def to_json(self) -> dict:
        return asdict(self)


def check_settings(project: Project) -> dict:
    """The `[check]` table of the config, validated; a bad value is a config error, not a finding."""
    settings = project.config.get("check", {})
    if not isinstance(settings, dict):
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: [check] must be a table")
    links = settings.get("links", [])
    if not isinstance(links, list) or not all(isinstance(path, str) and path.strip() for path in links):
        raise ConfigError(f"{CONFIG_FILE.as_posix()}: links under [check] must be a list of paths, not {links!r}")
    return {"links": [posixpath.normpath(path.strip().replace("\\", "/")) for path in links]}


def run_checks(project: Project, source: Source) -> list[Finding]:
    # Imported here: each check module imports `Finding` from this package.
    from keellay.checks import artifacts, front_matter, indexes, links, numbers

    settings = check_settings(project)
    found = artifacts.find(project, source)
    findings: list[Finding] = []
    findings += front_matter.check(found)
    findings += numbers.check(found, source)
    findings += indexes.check(project, source, found)
    findings += links.check(project, source, settings)
    return sorted(findings, key=lambda f: (f.file, f.line or 0, f.check, f.message))

"""The project's artifacts, found in their sections, with their front matter read as strings.

Where each kind lives follows `method/formats/`: change plans and deltas under `changes/` (open and archived), ideas
and the PRD under `product/`, ADRs, lessons and specs one file each next to their index (`README.md`).
"""

import posixpath
import re
from dataclasses import dataclass, field

import yaml

from keellay.checks.markdown import prefix_of
from keellay.checks.source import Source
from keellay.paths import Project

INDEX = "README.md"
# The letter of each numbered kind: a number is the letter and at least four digits, zero-padded to four (`C0007`,
# `I0004`, `A0012`, `L0003`), so numbering goes on after 9999 (`I10000`).
LETTERS = {"change": "C", "idea": "I", "adr": "A", "lesson": "L"}
# Any letters before the digits are taken here, so that a bare or wrongly lettered name is reported with the form it
# should have, instead of as a name without a number.
_NUMBERED = re.compile(r"^([A-Za-z]*\d{4,})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")


class FrontMatterError(Exception):
    def __init__(self, message: str, line: int | None = 1):
        super().__init__(message)
        self.line = line


@dataclass
class Artifact:
    kind: str  # change, delta, idea, prd, adr, lesson, spec, constitution
    file: str  # relative to the root
    name_id: str | None  # what the file or folder name says the artifact's ID is
    archived: bool = False
    meta: dict | None = None  # front matter, values as strings; None when it cannot be read
    meta_lines: dict = field(default_factory=dict)  # field -> line number in the file
    error: FrontMatterError | None = None
    folder: str | None = None  # for a plan or a delta: the change folder (`docs/changes/archive/C0007-x`)


def find(project: Project, source: Source) -> list[Artifact]:
    found: list[Artifact] = []
    constitution = section_path(project, "constitution")
    if constitution and source.is_file(constitution):
        found.append(Artifact("constitution", constitution, None))
    product = section_path(project, "product")
    if product:
        prd = prefix_of(product) + "prd.md"
        if source.is_file(prd):
            found.append(Artifact("prd", prd, None))
        found += _numbered(source, prefix_of(product) + "ideas", "idea")
    adr = section_path(project, "adr")
    if adr:
        found += _numbered(source, adr, "adr")
    lessons = section_path(project, "lessons")
    if lessons:
        found += _numbered(source, lessons, "lesson")
    specs = section_path(project, "specs")
    if specs:
        found += [Artifact("spec", name, posixpath.basename(name)[:-3]) for name in _files_in(source, specs)]
    changes = section_path(project, "changes")
    if changes:
        found += _changes(source, changes)
    for artifact in found:
        _read(source, artifact)
    return found


def section_path(project: Project, name: str) -> str | None:
    """The section's path when it is inside the root; a section in another repository is checked there."""
    path = project.sections[name].path
    if path is None:
        return None
    path = posixpath.normpath(path)
    return None if path == ".." or path.startswith("../") else path


def _files_in(source: Source, folder: str) -> list[str]:
    """Markdown files directly in the folder, without its index."""
    prefix = prefix_of(folder)
    return [
        name
        for name in source.files_under(folder)
        if name.endswith(".md") and "/" not in name[len(prefix) :] and posixpath.basename(name) != INDEX
    ]


def _numbered(source: Source, folder: str, kind: str) -> list[Artifact]:
    artifacts = []
    for name in _files_in(source, folder):
        match = _NUMBERED.match(posixpath.basename(name))
        artifacts.append(Artifact(kind, name, match.group(1) if match else None))
    return artifacts


def _changes(source: Source, changes: str) -> list[Artifact]:
    """Plans and deltas of open changes (`changes/<id>/`) and archived ones (`changes/archive/<id>/`)."""
    artifacts = []
    prefix = prefix_of(changes)
    for name in source.files_under(changes):
        parts = name[len(prefix) :].split("/")
        archived = parts[0] == "archive"
        if archived:
            parts = parts[1:]
        folder = prefix + ("archive/" if archived else "") + parts[0]
        if len(parts) == 2 and parts[1] == "plan.md":
            artifacts.append(Artifact("change", name, parts[0], archived, folder=folder))
        elif len(parts) == 3 and parts[1] == "delta" and parts[2].endswith(".md"):
            artifacts.append(Artifact("delta", name, parts[2][:-3], archived, folder=folder))
    return artifacts


def _read(source: Source, artifact: Artifact) -> None:
    try:
        artifact.meta, artifact.meta_lines = parse_front_matter(source.read(artifact.file))
    except FrontMatterError as error:
        artifact.error = error


def parse_front_matter(text: str) -> tuple[dict, dict]:
    """The front matter as a mapping of strings, and the line of each field.

    `BaseLoader` keeps every value a string, so `0012` stays `0012` and dates are not converted.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontMatterError("no front matter: the file must start with a line `---`")
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        raise FrontMatterError("front matter is not closed with a line `---`") from None
    try:
        meta = yaml.load("\n".join(lines[1:end]), Loader=yaml.BaseLoader)
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        line = mark.line + 2 if mark is not None else 1
        raise FrontMatterError(f"front matter is not valid YAML: {getattr(error, 'problem', error)}", line) from None
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise FrontMatterError("front matter must be a mapping of fields")
    positions = {}
    for index, line in enumerate(lines[1:end], start=2):
        key = re.match(r"^([A-Za-z][\w-]*)\s*:", line)
        if key:
            positions.setdefault(key.group(1), index)
    return meta, positions

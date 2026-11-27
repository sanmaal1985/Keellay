"""Check `links`: relative links in the project's Markdown point to a file or folder that exists.

Links in fenced code blocks and inline code are examples (a format shows files of an example project), links with
a URL scheme are not the project's files, and links that leave the root cannot be checked from the snapshot.
"""

import posixpath
import re
from collections.abc import Iterator
from urllib.parse import unquote

from keellay.checks import Finding
from keellay.checks.markdown import without_code_blocks
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "links"

_INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
# Link text may wrap onto the next line but not past a blank line (that is the next paragraph), and may hold one level
# of brackets, such as an image in a badge.
_TEXT = r"(?:[^\[\]\n]|\n(?![ \t]*\n))"
_INLINE_LINK = re.compile(rf"!?\[(?:{_TEXT}|\[{_TEXT}*\])*\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+[\"'(][^)]*)?\)")
_IMAGE = re.compile(rf"!\[{_TEXT}*\]\(\s*(<[^>\n]*>|[^)\s]+)(?:\s+[\"'(][^)]*)?\)")
# A reference definition is one line: the label, the destination, and at most a title after it.
_DEFINITION = re.compile(r"^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(<[^>\n]*>|\S+)(?:[ \t]+[\"'(][^\n]*)?[ \t]*$", re.MULTILINE)
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def markdown_files(project: Project, source: Source, extra: list[str]) -> list[str]:
    """`AGENTS.md`, the Markdown files of the sections inside the root, and the extra paths from the config."""
    roots = ["AGENTS.md", *extra]
    for section in project.sections.values():
        if section.path is not None:
            roots.append(posixpath.normpath(section.path))
    files: set[str] = set()
    for root in roots:
        if root.startswith(".."):
            continue
        files.update(name for name in source.files_under(root) if name.endswith(".md"))
    return sorted(files)


def links_in(text: str) -> Iterator[tuple[int, str]]:
    """Yield (line number, target) for every link outside code, in the order they appear."""
    # Inline code is blanked with spaces of the same length, so positions and line numbers stay where they were.
    prose = "\n".join(_INLINE_CODE.sub(lambda m: " " * len(m.group(0)), line) for line in without_code_blocks(text))
    targets: dict[int, str] = {}
    for pattern in (_INLINE_LINK, _IMAGE, _DEFINITION):
        for match in pattern.finditer(prose):
            targets.setdefault(match.start(1), match.group(1))
    for position in sorted(targets):
        yield prose.count("\n", 0, position) + 1, targets[position]


def target_path(file: str, target: str) -> str | None:
    """The path a link points to, relative to the root; None when it is not checked."""
    target = target.strip("<>").strip()
    if not target or target.startswith("#") or _SCHEME.match(target):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not target:
        return None
    if target.startswith("/"):
        path = posixpath.normpath(target.lstrip("/"))
    else:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(file), target))
    if path == ".." or path.startswith("../"):
        return None
    return "" if path == "." else path


def check(project: Project, source: Source, settings: dict[str, list[str]]) -> list[Finding]:
    findings = []
    for file in markdown_files(project, source, settings["links"]):
        for line, target in links_in(source.read(file)):
            path = target_path(file, target)
            if path is not None and not source.exists(path):
                findings.append(Finding(CHECK, "error", file, line, f"link to {target} points to nothing"))
    return findings

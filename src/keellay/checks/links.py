"""Check `links`: relative links in the project's Markdown point to a file or folder that exists.

Links in fenced code blocks and inline code are examples (a format shows files of an example project), links with
a URL scheme are not the project's files, and links that leave the root cannot be checked from the snapshot.
"""

import posixpath
import re
from urllib.parse import unquote

from keellay.checks import Finding
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "links"

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
_INLINE_CODE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_INLINE_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\[\]]*\])*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+[\"'(][^)]*)?\)")
_DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def markdown_files(project: Project, source: Source, extra: list[str]) -> list[str]:
    """`AGENTS.md`, the Markdown files of the sections inside the root, and the extra paths from the config."""
    roots = ["AGENTS.md", *extra]
    for section in project.sections.values():
        if section.path is not None:
            roots.append(posixpath.normpath(section.path))
    files = set()
    for root in roots:
        if root.startswith(".."):
            continue
        files.update(name for name in source.files_under(root) if name.endswith(".md"))
    return sorted(files)


def links_in(text: str):
    """Yield (line number, target) for every link outside code."""
    fence = None
    for number, line in enumerate(text.splitlines(), start=1):
        opening = _FENCE.match(line)
        if fence is not None:
            if opening and opening.group(1)[0] == fence[0] and len(opening.group(1)) >= len(fence):
                fence = None
            continue
        if opening:
            fence = opening.group(1)
            continue
        line = _INLINE_CODE.sub("", line)
        for match in _INLINE_LINK.finditer(line):
            yield number, match.group(1)
        definition = _DEFINITION.match(line)
        if definition:
            yield number, definition.group(1)


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


def check(project: Project, source: Source, settings: dict) -> list[Finding]:
    findings = []
    for file in markdown_files(project, source, settings["links"]):
        for line, target in links_in(source.read(file)):
            path = target_path(file, target)
            if path is not None and not source.exists(path):
                findings.append(Finding(CHECK, "error", file, line, f"link to {target} points to nothing"))
    return findings

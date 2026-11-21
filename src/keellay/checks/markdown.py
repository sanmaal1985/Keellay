"""Markdown helpers shared by the checks: what is prose and what is a code example."""

import re

_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def without_code_blocks(text: str) -> list[str]:
    """The lines of the text, with every line of a fenced code block (fences included) blanked.

    Line numbers stay as they are, so a finding still points to the right line. Code blocks hold examples: a format
    shows the files of an example project, a spec may show a delta.
    """
    lines, fence = [], None
    for line in text.splitlines():
        opening = _FENCE.match(line)
        if fence is not None:
            if opening and opening.group(1)[0] == fence[0] and len(opening.group(1)) >= len(fence):
                fence = None
            lines.append("")
            continue
        if opening:
            fence = opening.group(1)
            lines.append("")
            continue
        lines.append(line)
    return lines


def prefix_of(folder: str) -> str:
    """The prefix of the paths inside a folder: `docs/adr/` for `docs/adr`, nothing for the root."""
    folder = folder.strip("/")
    return "" if folder in ("", ".") else folder + "/"

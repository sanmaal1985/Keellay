"""Markdown helpers shared by the checks: what is prose and what is a code example."""

import re
from dataclasses import dataclass

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


@dataclass
class Section:
    line: int  # the line of its `## ` heading
    body: list[tuple[int, str]]  # (line number, text) of every line up to the next `#` or `##` heading

    def is_empty(self) -> bool:
        return not any(text.strip() for _, text in self.body)

    def items(self) -> list[tuple[int, str]]:
        """Top-level list items: a nested item or a wrapped line belongs to the item above it."""
        return [(number, text) for number, text in self.body if _ITEM.match(text)]

    def text(self) -> str:
        return "\n".join(text for _, text in self.body)


_ITEM = re.compile(r"^[-*+]\s+\S")


def section(text: str, title: str) -> Section | None:
    """The `## <title>` section of a Markdown file, outside code blocks, or None when there is none."""
    lines = without_code_blocks(text)
    heading = re.compile(rf"^##\s+{re.escape(title)}\s*$")
    start = next((index for index, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return None
    body = []
    for index in range(start + 1, len(lines)):
        if re.match(r"^#{1,2}\s", lines[index]):
            break
        body.append((index + 1, lines[index]))
    return Section(start + 1, body)


def prefix_of(folder: str) -> str:
    """The prefix of the paths inside a folder: `docs/adr/` for `docs/adr`, nothing for the root."""
    folder = folder.strip("/")
    return "" if folder in ("", ".") else folder + "/"

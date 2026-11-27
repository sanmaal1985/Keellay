"""Check `index`: each section's index (`README.md`) lists every item once, in the table that matches its status,
with the item's own status, and every row points to an item.

The tables and the statuses each one holds follow the index examples in `method/formats/`. A table is named by the
line just above it ("In force:", "Ideas, open (in order of priority):").
"""

import posixpath
import re
from dataclasses import dataclass

from keellay.checks import Finding
from keellay.checks.artifacts import INDEX, Artifact
from keellay.checks.markdown import prefix_of, without_code_blocks
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "index"

_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)>?[^)]*\)")


@dataclass(frozen=True)
class Table:
    label: str  # the line above the table, without a trailing colon
    status_column: int | None
    rows: list[tuple[int, list[str]]]  # (line number, cells)


@dataclass(frozen=True)
class IndexRule:
    kind: str
    archived: bool  # the index lists archived items too
    tables: dict[str, tuple[str, ...]] | None  # label prefix -> statuses it holds; None: one table with every item


RULES = {
    "changes": IndexRule("change", False, None),
    "specs": IndexRule("spec", False, None),
    "adr": IndexRule("adr", False, {"In force": ("accepted",), "Replaced": ("superseded",)}),
    "lessons": IndexRule("lesson", False, {"Active": ("active",), "Mechanized": ("mechanized",)}),
    "product": IndexRule(
        "idea", False, {"Ideas, open": ("new", "assessed", "planned"), "Ideas, closed": ("done", "declined")}
    ),
}


def check(project: Project, source: Source, artifacts: list[Artifact]) -> list[Finding]:
    findings = []
    for section, rule in RULES.items():
        path = project.sections[section].path
        if path is None or path.startswith(".."):
            continue
        items = [a for a in artifacts if a.kind == rule.kind and (rule.archived or not a.archived)]
        findings += _check_index(posixpath.normpath(path), source, rule, items, artifacts)
    return findings


def _status(artifact: Artifact) -> str | None:
    """The item's status; a status that is not a string is a front-matter finding, not something to index by."""
    status = (artifact.meta or {}).get("status")
    return status if isinstance(status, str) else None


def _check_index(
    folder: str, source: Source, rule: IndexRule, items: list[Artifact], every: list[Artifact]
) -> list[Finding]:
    index = prefix_of(folder) + INDEX
    expected = [item for item in items if rule.tables is None or _status(item) in _all_statuses(rule)]
    if not source.is_file(index):
        if expected:
            return [
                Finding(
                    CHECK,
                    "error",
                    index,
                    None,
                    f"the index is missing; it must list {len(expected)} {rule.kind} file(s)",
                )
            ]
        return []

    def finding(line: int | None, message: str) -> Finding:
        return Finding(CHECK, "error", index, line, message)

    by_file = {item.file: item for item in items}
    other_files = {artifact.file for artifact in every if artifact.kind == rule.kind} - set(by_file)
    findings: list[Finding] = []
    listed: dict[str, int] = {}
    for table in _tables(source.read(index)):
        statuses = _statuses_for(rule, table.label)
        if rule.tables is not None and statuses is None:
            continue  # a table the format does not define, such as a list of links
        for line, cells in table.rows:
            link = _LINK.search(cells[0]) if cells else None
            if link is None:
                continue
            target = posixpath.normpath(posixpath.join(folder, link.group(1).split("#", 1)[0]))
            item = by_file.get(target)
            if item is None:
                reason = "is not open" if target in other_files else "is not one of the section's files"
                findings.append(finding(line, f"row for {link.group(1)}: the {rule.kind} {reason}"))
                continue
            if target in listed:
                findings.append(finding(line, f"{target} is listed again (first on line {listed[target]})"))
                continue
            listed[target] = line
            status = _status(item)
            if statuses is not None and status not in statuses:
                findings.append(finding(line, f"{target} has status {status!r} but is listed under {table.label!r}"))
            if table.status_column is not None and table.status_column < len(cells) and status is not None:
                shown = cells[table.status_column].strip()
                if shown != status:
                    findings.append(finding(line, f"{target} is listed as {shown!r} but its status is {status!r}"))
    for item in expected:
        if item.file not in listed:
            findings.append(finding(None, f"{item.file} ({_status(item) or 'no status'}) is not listed"))
    return findings


def _all_statuses(rule: IndexRule) -> set[str]:
    if rule.tables is None:
        return set()
    return {status for statuses in rule.tables.values() for status in statuses}


def _statuses_for(rule: IndexRule, label: str) -> tuple[str, ...] | None:
    if rule.tables is None:
        return None
    for prefix, statuses in rule.tables.items():
        if label.startswith(prefix):
            return statuses
    return None


def _tables(text: str) -> list[Table]:
    """Markdown tables outside code blocks, each with the line above it as its label."""
    tables, label = [], ""
    lines = without_code_blocks(text)
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        delimiter = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if stripped.startswith("|") and re.match(r"^\|[\s:|-]+\|$", delimiter):
            header = _cells(stripped)
            status_column = next((i for i, cell in enumerate(header) if cell.lower() == "status"), None)
            rows = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append((index + 1, _cells(lines[index].strip())))
                index += 1
            tables.append(Table(label, status_column, rows))
            continue
        if stripped:
            label = stripped.rstrip(":").strip()
        index += 1
    return tables


def _cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip("|").split("|")]

"""The `prd` check: every area of the PRD has its ID, its lines and a known status, and plans name only real areas.

An area is a `###` heading under `## Areas`; its lines are top-level list items (`- Status: planned`). The In / Out
line starts with `In:` (`- In: manual entry. Out: bank import.`). Measure is optional at level light. Archived plans
are history and are not checked. A project without a PRD file has nothing to check here.
"""

import re

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact
from keellay.checks.markdown import section, without_code_blocks
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "prd"
STATUSES = ("planned", "in-progress", "delivered", "dropped")
AREA_ID = r"PRD-[a-z0-9]+(?:-[a-z0-9]+)*"
_HEADING = re.compile(rf"^###\s+({AREA_ID}):\s+\S")
_LINE = re.compile(r"^[-*+]\s+(Outcome|Measure|In(?:\s*/\s*Out)?|Status)\s*:(.*)$")
_REFERENCE = re.compile(rf"(?<![A-Za-z0-9-]){AREA_ID}(?![A-Za-z0-9-])")


def check(project: Project, artifacts: list[Artifact], source: Source) -> list[Finding]:
    prd = next((artifact for artifact in artifacts if artifact.kind == "prd"), None)
    if prd is None:
        return []
    required = ("Outcome", "In", "Status") + (("Measure",) if project.level != "light" else ())
    areas, findings = _areas(prd, source.read(prd.file), required)
    for plan in artifacts:
        if plan.kind == "change" and not plan.archived:
            findings += _references(plan, source.read(plan.file), areas)
    return findings


def _areas(prd: Artifact, text: str, required: tuple[str, ...]) -> tuple[set[str], list[Finding]]:
    """The area IDs of the PRD, and what is wrong with its areas."""
    found = section(text, "Areas")
    if found is None:
        return set(), []
    findings: list[Finding] = []
    first: dict[str, int] = {}
    areas: list[tuple[str, int, dict]] = []  # (ID, line of the heading, field -> (value, line))
    for number, line in found.body:
        if line.startswith("### "):
            heading = _HEADING.match(line)
            if heading is None:
                findings.append(_finding(prd, number, f"area heading `{line.strip()}` is not "
                                                      f"`### PRD-<topic>: <outcome>`"))
                areas.append(("", number, {}))  # its lines are not taken for the area above
                continue
            area = heading.group(1)
            if area in first:
                findings.append(_finding(prd, number, f"{area} is used by two headings, at lines {first[area]} and "
                                                      f"{number}; an area ID is unique"))
            first.setdefault(area, number)
            areas.append((area, number, {}))
            continue
        item = _LINE.match(line)
        if item and areas:
            name = "In" if item.group(1).startswith("In") else item.group(1)
            areas[-1][2].setdefault(name, (item.group(2).strip(), number))
    for area, number, fields in areas:
        if not area:
            continue
        for name in required:
            if name not in fields:
                label = "In / Out" if name == "In" else name
                findings.append(_finding(prd, number, f"{area} has no `{label}` line"))
        if "Status" in fields:
            value, line = fields["Status"]
            status = value.strip("`").strip()
            if status not in STATUSES:
                findings.append(_finding(prd, line, f"{area}: Status is `{status}`; expected one of "
                                                    f"{', '.join(STATUSES)}"))
    return set(first), findings


def _references(plan: Artifact, text: str, areas: set[str]) -> list[Finding]:
    findings, seen = [], set()
    for number, line in enumerate(without_code_blocks(text), start=1):
        for match in _REFERENCE.finditer(line):
            area = match.group(0)
            if area not in areas and area not in seen:
                seen.add(area)
                findings.append(_finding(plan, number, f"the plan names {area}, which is not an area of the PRD"))
    return findings


def _finding(artifact: Artifact, line: int | None, message: str) -> Finding:
    return Finding(CHECK, "error", artifact.file, line, message)

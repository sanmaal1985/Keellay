"""The `requirements` check: every requirement of a living spec, and every ADDED or MODIFIED one of an open change's
delta, has a statement with "shall" and a scenario with a WHEN and a THEN line; at level strict it has a `Verified by`
line whose test files exist.

A requirement is a `### REQ-...` heading and everything up to the next `###` or higher heading; its scenarios are its
`#### Scenario` headings. The delta check reads requirements the same way, so the parser lives here.
"""

import re
from dataclasses import dataclass

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact
from keellay.checks.markdown import without_code_blocks
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "requirements"
CHECKED_IN_DELTAS = ("ADDED", "MODIFIED")  # REMOVED carries only the ID, the title and the reason
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_REQUIREMENT = re.compile(r"^(REQ-[A-Za-z0-9-]+?)(?::|\s|$)")
_SCENARIO = re.compile(r"^Scenario\b")
_STEP = re.compile(r"^\s*[-*+]\s+(GIVEN|WHEN|THEN|AND)\b")
_SHALL = re.compile(r"\bshall\b")
_VERIFIED_BY = re.compile(r"^Verified by:")
_CODE_SPAN = re.compile(r"`([^`]+)`")


@dataclass
class Requirement:
    id: str
    line: int  # the line of its heading
    section: str | None  # the `##` heading it is under: `Requirements` in a spec, `ADDED` in a delta
    body: list[tuple[int, str]]  # (line number, text) up to the next `###` or higher heading


def parse(text: str) -> list[Requirement]:
    """The requirements of a spec or a delta, outside code blocks."""
    found: list[Requirement] = []
    current: Requirement | None = None
    section: str | None = None
    for number, line in enumerate(without_code_blocks(text), start=1):
        heading = _HEADING.match(line)
        if heading and len(heading.group(1)) <= 3:
            current = None
            if len(heading.group(1)) <= 2:
                section = heading.group(2) if len(heading.group(1)) == 2 else None
                continue
            requirement = _REQUIREMENT.match(heading.group(2))
            if requirement:
                current = Requirement(requirement.group(1), number, section, [])
                found.append(current)
            continue
        if current is not None:
            current.body.append((number, line))
    return found


def check(project: Project, artifacts: list[Artifact], source: Source) -> list[Finding]:
    findings: list[Finding] = []
    for artifact in artifacts:
        if artifact.kind == "spec":
            checked = parse(source.read(artifact.file))
        elif artifact.kind == "delta" and not artifact.archived:
            checked = [item for item in parse(source.read(artifact.file)) if item.section in CHECKED_IN_DELTAS]
        else:
            continue
        for requirement in checked:
            findings += _problems(artifact, requirement, project.level == "strict", source)
    return findings


def _problems(artifact: Artifact, requirement: Requirement, strict: bool, source: Source) -> list[Finding]:
    findings = []
    statement, scenarios = _split(requirement.body)
    if not any(_SHALL.search(text) for _, text in statement if not _VERIFIED_BY.match(text)):
        findings.append(_finding(artifact, requirement.line, f"{requirement.id} has no statement with \"shall\""))
    if not scenarios:
        findings.append(_finding(artifact, requirement.line, f"{requirement.id} has no `#### Scenario:`"))
    elif not any(_has_steps(steps) for steps in scenarios):
        findings.append(_finding(artifact, requirement.line,
                                 f"{requirement.id} has no scenario with a WHEN and a THEN line"))
    if strict:
        findings += _verified_by(artifact, requirement, statement, source)
    return findings


def _split(body: list[tuple[int, str]]) -> tuple[list[tuple[int, str]], list[list[str]]]:
    """The lines before the first scenario, and the lines of each scenario."""
    statement: list[tuple[int, str]] = []
    scenarios: list[list[str]] = []
    in_scenario = False
    for number, text in body:
        heading = _HEADING.match(text)
        if heading:
            in_scenario = bool(_SCENARIO.match(heading.group(2)))
            if in_scenario:
                scenarios.append([])
            continue
        if in_scenario:
            scenarios[-1].append(text)
        elif not scenarios:
            statement.append((number, text))
    return statement, scenarios


def _has_steps(lines: list[str]) -> bool:
    steps = {match.group(1) for match in map(_STEP.match, lines) if match}
    return {"WHEN", "THEN"} <= steps


def _verified_by(artifact: Artifact, requirement: Requirement, statement: list[tuple[int, str]],
                 source: Source) -> list[Finding]:
    start = next((index for index, (_, text) in enumerate(statement) if _VERIFIED_BY.match(text)), None)
    if start is None:
        later = next((number for number, text in requirement.body if _VERIFIED_BY.match(text)), None)
        if later is not None:
            return [_finding(artifact, later, f"{requirement.id}: the `Verified by` line goes before the first "
                                              f"scenario, after the statement")]
        return [_finding(artifact, requirement.line, f"{requirement.id} has no `Verified by` line, which level strict "
                                                     f"requires")]
    number = statement[start][0]
    paragraph = []
    for _, text in statement[start:]:  # a long list of tests wraps onto the next lines
        if not text.strip():
            break
        paragraph.append(text)
    tests = _CODE_SPAN.findall(" ".join(paragraph))
    if not tests:
        return [_finding(artifact, number, f"{requirement.id}: `Verified by` names no test")]
    findings = []
    for test in tests:
        path = test.split("::", 1)[0].strip()
        if not source.is_file(path):
            findings.append(_finding(artifact, number, f"{requirement.id}: `Verified by` names {path}, which does "
                                                       f"not exist"))
    return findings


def _finding(artifact: Artifact, line: int | None, message: str) -> Finding:
    return Finding(CHECK, "error", artifact.file, line, message)

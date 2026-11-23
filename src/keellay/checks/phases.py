"""The `phases` check: every phase of an open change's plan says who does it, after what, and when it is done.

A phase is a `###` heading under `## Phases`; its fields are top-level list items (`- Role: developer`). Archived
plans are history and are not checked: the format may have changed since they closed.
"""

import re
from dataclasses import dataclass, field

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact
from keellay.checks.markdown import without_code_blocks
from keellay.checks.source import Source

CHECK = "phases"
CORE_ROLES = ("architect", "developer", "product-owner", "manager")
FIELDS = ("Role", "Depends on", "Done when")
_ROLE = re.compile(r"^(?:%s)(?:-[a-z0-9]+(?:-[a-z0-9]+)*)?$" % "|".join(re.escape(role) for role in CORE_ROLES))
_FIELD = re.compile(r"^[-*]\s+(Role|Depends on|Done when)\s*:(.*)$")
_NUMBERED_HEADING = re.compile(r"^###\s+(\d+)\.")


@dataclass
class Phase:
    name: str  # "phase 2", or the heading text when the heading has no number
    number: str | None
    line: int
    fields: dict = field(default_factory=dict)  # field name -> (value, line)


def check(artifacts: list[Artifact], source: Source) -> list[Finding]:
    findings = []
    for plan in artifacts:
        if plan.kind != "change" or plan.archived or plan.meta is None:
            continue
        findings += _check_plan(plan, source.read(plan.file))
    return findings


def _check_plan(plan: Artifact, text: str) -> list[Finding]:
    found = _phases(text)
    if found is None or not found[1]:
        status = plan.meta.get("status")
        if status and status != "draft":
            line = found[0] if found else None
            return [_finding(plan, line, f"the plan is `{status}` and has no phase; phases are cut before the owner "
                                         f"approves the plan")]
        return []
    phases = found[1]
    numbers = {phase.number for phase in phases if phase.number}
    findings = []
    for phase in phases:
        for name in FIELDS:
            if name not in phase.fields:
                findings.append(_finding(plan, phase.line, f"{phase.name} has no `{name}` line"))
        if "Role" in phase.fields:
            role, line = phase.fields["Role"]
            if not _ROLE.match(role):
                findings.append(_finding(plan, line, f"{phase.name}: unknown role `{role}`; a role is one of "
                                                     f"{', '.join(CORE_ROLES)} or an instance `<core role>-<qualifier>`"))
        if "Depends on" in phase.fields:
            value, line = phase.fields["Depends on"]
            for number in re.findall(r"\d+", value):
                if number.lstrip("0") not in {n.lstrip("0") for n in numbers}:
                    findings.append(_finding(plan, line, f"{phase.name} depends on phase {number}, which the plan "
                                                         f"does not have"))
    return findings


def _phases(text: str) -> tuple[int, list[Phase]] | None:
    """The line of `## Phases` and the phases under it, or None when the plan has no such section."""
    lines = without_code_blocks(text)
    start = next((index for index, line in enumerate(lines) if re.match(r"^##\s+Phases\s*$", line)), None)
    if start is None:
        return None
    phases: list[Phase] = []
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if re.match(r"^##\s", line):
            break
        if line.startswith("### "):
            number = _NUMBERED_HEADING.match(line)
            name = f"phase {number.group(1)}" if number else f"phase `{line[4:].strip()}`"
            phases.append(Phase(name, number.group(1) if number else None, index + 1))
            continue
        item = _FIELD.match(line)
        if item and phases:
            value = item.group(2).strip().strip("`").strip()
            phases[-1].fields.setdefault(item.group(1), (value, index + 1))
    return start + 1, phases


def _finding(plan: Artifact, line: int | None, message: str) -> Finding:
    return Finding(CHECK, "error", plan.file, line, message)

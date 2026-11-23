"""Check `numbers`: a number belongs to one change, idea, ADR or lesson, and a requirement ID to one requirement of
its spec, with the spec's prefix."""

import re
from collections import defaultdict

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact
from keellay.checks.markdown import without_code_blocks
from keellay.checks.source import Source

CHECK = "numbers"
NUMBERED_KINDS = ("change", "idea", "adr", "lesson")
REQUIREMENT = re.compile(r"^#{2,6}\s+(REQ-[A-Za-z0-9-]+?)(?::|\s|$)")


def check(artifacts: list[Artifact], source: Source) -> list[Finding]:
    return _shared_numbers(artifacts) + _requirement_ids(artifacts, source)


def _number(artifact: Artifact) -> str | None:
    if artifact.name_id is None:
        return None
    # The whole number with its letter (`C0007`); a misnamed file is reported by `front-matter`.
    match = re.match(r"^([A-Za-z]*\d{4})(?:-|$)", artifact.name_id)
    return match.group(1) if match else None


def _shared_numbers(artifacts: list[Artifact]) -> list[Finding]:
    owners: dict[tuple[str, str], list[Artifact]] = defaultdict(list)
    for artifact in artifacts:
        number = _number(artifact) if artifact.kind in NUMBERED_KINDS else None
        if number is not None:
            owners[(artifact.kind, number)].append(artifact)
    findings = []
    for (kind, number), group in sorted(owners.items()):
        if len(group) < 2:
            continue
        files = sorted(artifact.file for artifact in group)
        for file in files[1:]:
            others = ", ".join(other for other in files if other != file)
            findings.append(Finding(CHECK, "error", file, None, f"{kind} number {number} is also used by {others}"))
    return findings


def _requirement_ids(artifacts: list[Artifact], source: Source) -> list[Finding]:
    findings = []
    for spec in (artifact for artifact in artifacts if artifact.kind == "spec"):
        prefix = (spec.meta or {}).get("prefix")
        seen: dict[str, int] = {}
        # Headings in code blocks are examples, such as a delta shown in the spec.
        for line_number, line in enumerate(without_code_blocks(source.read(spec.file)), start=1):
            match = REQUIREMENT.match(line)
            if not match:
                continue
            requirement = match.group(1)
            own_form = rf"REQ-{re.escape(prefix)}-\d{{3}}" if isinstance(prefix, str) and prefix else None
            if own_form and not re.fullmatch(own_form, requirement):
                findings.append(Finding(CHECK, "error", spec.file, line_number,
                                        f"{requirement} does not have the form REQ-{prefix}-<nnn> of this spec"))
            if requirement in seen:
                findings.append(Finding(CHECK, "error", spec.file, line_number,
                                        f"{requirement} is already used on line {seen[requirement]}"))
            else:
                seen[requirement] = line_number
    return findings

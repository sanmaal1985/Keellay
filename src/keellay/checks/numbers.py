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
    return _number_of(artifact.name_id)


def _owners(artifacts: list[Artifact]) -> dict[tuple[str, str], set[str]]:
    """(kind, number) -> the files, or for a change the folders, that use it.

    A change is its folder: the one with a plan, and also one that only holds deltas, as in a repository whose plans
    live in another one.
    """
    owners: dict[tuple[str, str], set[str]] = defaultdict(set)
    for artifact in artifacts:
        if artifact.kind in ("change", "delta") and artifact.folder is not None:
            number = _number_of(artifact.folder.rsplit("/", 1)[-1])
            if number is not None:
                owners[("change", number)].add(artifact.folder)
        elif artifact.kind in NUMBERED_KINDS:
            number = _number(artifact)
            if number is not None:
                owners[(artifact.kind, number)].add(artifact.file)
    return owners


def _number_of(name: str) -> str | None:
    match = re.match(r"^([A-Za-z]*\d{4,})(?:-|$)", name)
    return match.group(1) if match else None


def _shared_numbers(artifacts: list[Artifact]) -> list[Finding]:
    findings = []
    for (kind, number), group in sorted(_owners(artifacts).items()):
        if len(group) < 2:
            continue
        files = sorted(group)
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

"""The `ideas` check: an idea keeps the verdict, outcome and links its status needs.

A field whose form is wrong is the front-matter check's finding; this one reads only values of the right form. The
changes an idea may name are the plans of open and archived changes, and the change folders that hold only deltas, as
in a repository whose plans live in another one; whether such a change is closed cannot be seen here, so it is not
checked. Areas are the `### PRD-<topic>` headings of the PRD; a project without a PRD file has no areas to compare
with, so `prd` is not checked there.
"""

import posixpath
import re

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact
from keellay.checks.front_matter import CHANGE_ID
from keellay.checks.markdown import section, without_code_blocks
from keellay.checks.source import Source

CHECK = "ideas"
_AREA = re.compile(r"^###\s+(PRD-[a-z0-9]+(?:-[a-z0-9]+)*)\b")


def check(artifacts: list[Artifact], source: Source) -> list[Finding]:
    changes = known_changes(artifacts)
    areas = _areas(artifacts, source)
    findings = []
    for idea in artifacts:
        if idea.kind == "idea" and idea.meta is not None:
            findings += _check_idea(idea, source.read(idea.file), changes, areas)
    return findings


def known_changes(artifacts: list[Artifact]) -> dict[str, Artifact | None]:
    """Change ID -> its plan, or None for a change folder that holds only deltas."""
    changes: dict[str, Artifact | None] = {}
    for artifact in artifacts:
        if artifact.kind == "change":
            changes[artifact.name_id] = artifact
    for artifact in artifacts:
        if artifact.kind == "delta" and artifact.folder:
            changes.setdefault(posixpath.basename(artifact.folder), None)
    return changes


def _areas(artifacts: list[Artifact], source: Source) -> set[str] | None:
    prd = next((artifact for artifact in artifacts if artifact.kind == "prd"), None)
    if prd is None:
        return None
    return {match.group(1) for line in without_code_blocks(source.read(prd.file)) if (match := _AREA.match(line))}


def _value(meta: dict, name: str) -> str:
    value = meta.get(name)
    return value.strip() if isinstance(value, str) else ""


def _check_idea(idea: Artifact, text: str, changes: dict, areas: set[str] | None) -> list[Finding]:
    meta, lines = idea.meta, idea.meta_lines

    def finding(field: str, message: str) -> Finding:
        return Finding(CHECK, "error", idea.file, lines.get(field, lines.get("status", 1)), message)

    findings = []
    status, verdict = _value(meta, "status"), _value(meta, "verdict")
    if not verdict:
        if status == "assessed":
            findings.append(finding("verdict", "the idea is `assessed` and has no `verdict`"))
        elif status in ("planned", "done", "declined"):
            assessment = section(text, "Assessment")
            if assessment is None or assessment.is_empty():
                findings.append(finding("verdict", f"the idea is `{status}` with no `verdict` and an empty Assessment; "
                                                   f"a skipped verdict is explained there"))
    if status == "declined":
        outcome = section(text, "Outcome")
        if outcome is None or outcome.is_empty():
            findings.append(finding("status", "the idea is `declined` and its Outcome does not say why"))
    change = _value(meta, "change")
    if change and CHANGE_ID.fullmatch(change):
        if change not in changes:
            findings.append(finding("change", f"`change` names `{change}`, which is not a change, open or archived"))
        elif status == "done" and changes[change] is not None:
            change_status = _value(changes[change].meta or {}, "status")
            if change_status != "closed":
                findings.append(finding("change", f"the idea is `done` but its change `{change}` is "
                                                  f"`{change_status or 'without a status'}`, not `closed`"))
    prd = _value(meta, "prd")
    if prd and areas is not None and re.fullmatch(r"PRD-[a-z0-9]+(?:-[a-z0-9]+)*", prd) and prd not in areas:
        findings.append(finding("prd", f"`prd` names `{prd}`, which is not an area of the PRD"))
    return findings

"""The `deltas` check: an open change's delta agrees with the living spec it changes, and no requirement is touched by
two open changes.

A delta changes the spec `<specs>/<capability>.md`, the capability taken from its front matter or else its file name.
MODIFIED and REMOVED name requirements the spec has; ADDED ones it does not have yet. A delta for a capability with no
spec starts one, so it only adds and carries the spec's `prefix`. A `##` section other than these and Purpose would
hide its requirements from both checks, so it is reported. Archived deltas are merged history and are not checked, nor
is a delta whose front matter cannot be read: `front-matter` reports it. When the specs are in another repository,
the deltas are there too and are checked there.
"""

import re
from collections import defaultdict

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact, section_path
from keellay.checks.markdown import without_code_blocks
from keellay.checks.requirements import parse
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "deltas"
TOUCHING = ("ADDED", "MODIFIED", "REMOVED")
SECTIONS = TOUCHING + ("Purpose",)
_SECTION = re.compile(r"^##\s+(.*?)\s*$")


def check(project: Project, artifacts: list[Artifact], source: Source) -> list[Finding]:
    if section_path(project, "specs") is None:
        return []
    specs = {artifact.name_id: artifact for artifact in artifacts if artifact.kind == "spec"}
    findings: list[Finding] = []
    touched: dict[str, list[tuple[Artifact, int]]] = defaultdict(list)
    for delta in artifacts:
        if delta.kind != "delta" or delta.archived or delta.meta is None:
            continue
        meta = delta.meta
        capability = meta.get("capability") or delta.name_id
        spec = specs.get(capability)
        in_spec = {requirement.id for requirement in parse(source.read(spec.file))} if spec else set()
        text = source.read(delta.file)
        for number, line in enumerate(without_code_blocks(text), start=1):
            section = _SECTION.match(line)
            if section and section.group(1) not in SECTIONS:
                findings.append(_finding(delta, number, f"section `## {section.group(1)}` is not one of "
                                                        f"{', '.join(SECTIONS)}; its requirements are not read"))
        for requirement in parse(text):
            if requirement.section not in TOUCHING:
                continue
            touched[requirement.id].append((delta, requirement.line))
            where = requirement.section
            if spec is None:
                if where != "ADDED":
                    findings.append(_finding(delta, requirement.line, f"{requirement.id} is under {where}, but "
                                                                      f"capability {capability} has no spec yet"))
            elif where == "ADDED" and requirement.id in in_spec:
                findings.append(_finding(delta, requirement.line, f"{requirement.id} is under ADDED, but {spec.file} "
                                                                  f"already has it"))
            elif where != "ADDED" and requirement.id not in in_spec:
                findings.append(_finding(delta, requirement.line, f"{requirement.id} is under {where}, but {spec.file} "
                                                                  f"does not have it"))
        if spec is None and not meta.get("prefix"):
            findings.append(_finding(delta, delta.meta_lines.get("capability", 1),
                                     f"capability {capability} has no spec yet, so the delta starts one and needs "
                                     f"`prefix` in its front matter"))
    for requirement, uses in touched.items():
        changes = sorted({_change(delta) for delta, _ in uses})
        if len(changes) < 2:
            continue
        for delta, line in uses:
            others = ", ".join(change for change in changes if change != _change(delta))
            findings.append(_finding(delta, line, f"{requirement} is also touched by open change {others}; one "
                                                  f"requirement is changed by one open change at a time"))
    return findings


def _change(delta: Artifact) -> str:
    assert delta.folder is not None  # every delta is found in a change folder
    return delta.folder.rsplit("/", 1)[-1]


def _finding(artifact: Artifact, line: int | None, message: str) -> Finding:
    return Finding(CHECK, "error", artifact.file, line, message)

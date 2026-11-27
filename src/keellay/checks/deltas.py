"""The `deltas` check: an open change's delta agrees with the living spec it changes, and no requirement is touched by
two open changes.

A delta changes the spec `<specs>/<capability>.md`, the capability taken from its front matter or else its file name.
MODIFIED and REMOVED name requirements the spec has; ADDED ones it does not have yet. A delta for a capability with no
spec starts one, so it only adds and carries the spec's `prefix`. Archived deltas are merged history and are not
checked. When the specs are in another repository, the deltas are there too and are checked there.
"""

from collections import defaultdict

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact, section_path
from keellay.checks.requirements import parse
from keellay.checks.source import Source
from keellay.paths import Project

CHECK = "deltas"
TOUCHING = ("ADDED", "MODIFIED", "REMOVED")


def check(project: Project, artifacts: list[Artifact], source: Source) -> list[Finding]:
    if section_path(project, "specs") is None:
        return []
    specs = {artifact.name_id: artifact for artifact in artifacts if artifact.kind == "spec"}
    findings: list[Finding] = []
    touched: dict[str, list[tuple[Artifact, int]]] = defaultdict(list)
    for delta in artifacts:
        if delta.kind != "delta" or delta.archived:
            continue
        meta = delta.meta or {}
        capability = meta.get("capability") or delta.name_id
        spec = specs.get(capability)
        in_spec = {requirement.id for requirement in parse(source.read(spec.file))} if spec else set()
        for requirement in parse(source.read(delta.file)):
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
    return (delta.folder or delta.file).rsplit("/", 1)[-1]


def _finding(artifact: Artifact, line: int | None, message: str) -> Finding:
    return Finding(CHECK, "error", artifact.file, line, message)

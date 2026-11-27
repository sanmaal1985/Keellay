"""The `adr` check: `supersedes` and `superseded-by` name each other, and the status agrees with them.

Each link between a new ADR and the one it replaces is written twice, once on each side; a side that is missing is
reported on the ADR that should carry it. Values of the wrong form are the front-matter check's findings.
"""

import re

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact

CHECK = "adr"
_ADR = re.compile(r"A(?:\d{4}|[1-9]\d{4,})")


def check(artifacts: list[Artifact]) -> list[Finding]:
    adrs = {_id(adr): adr for adr in artifacts if adr.kind == "adr" and adr.meta is not None and _id(adr)}
    findings = []
    for adr_id, adr in sorted(adrs.items()):
        for name in ("supersedes", "superseded-by"):
            if adr_id in _ids(adr.meta, name):
                findings.append(_finding(adr, name, f"`{name}` names {adr_id} itself; it names another ADR"))
    # A link of an ADR to itself is reported above, not as a pair with a missing side.
    replaces = {(new, old) for new, adr in adrs.items() for old in _ids(adr.meta, "supersedes") if old != new}
    replaced = {(new, old) for old, adr in adrs.items() for new in _ids(adr.meta, "superseded-by") if new != old}
    for new, old in sorted(replaces - replaced):
        if old in adrs:
            findings.append(
                _finding(
                    adrs[old],
                    "superseded-by",
                    f"{new} supersedes {old}, but {old}'s `superseded-by` does not name {new}",
                )
            )
        else:
            findings.append(_finding(adrs[new], "supersedes", f"`supersedes` names {old}, which is not an ADR here"))
    for new, old in sorted(replaced - replaces):
        if new in adrs:
            findings.append(
                _finding(
                    adrs[new],
                    "supersedes",
                    f"{old} is superseded by {new}, but {new}'s `supersedes` does not name {old}",
                )
            )
        else:
            findings.append(
                _finding(adrs[old], "superseded-by", f"`superseded-by` names {new}, which is not an ADR here")
            )
    for adr_id, adr in sorted(adrs.items()):
        status = adr.meta.get("status")
        superseded_by = _ids(adr.meta, "superseded-by")
        if status == "superseded" and not superseded_by and not any(old == adr_id for _, old in replaces):
            findings.append(
                _finding(
                    adr, "status", "the ADR is `superseded` and `superseded-by` does not name the ADR that replaced it"
                )
            )
        if superseded_by and status != "superseded":
            findings.append(
                _finding(
                    adr,
                    "status",
                    f"`superseded-by` names {', '.join(superseded_by)} but the status is `{status}`, not `superseded`",
                )
            )
    return findings


def _id(adr: Artifact) -> str | None:
    value = adr.meta.get("id")
    return value if isinstance(value, str) and _ADR.fullmatch(value) else None


def _ids(meta: dict, name: str) -> list[str]:
    value = meta.get(name)
    values = value if isinstance(value, list) else [value]
    return [item for item in values if isinstance(item, str) and _ADR.fullmatch(item)]


def _finding(adr: Artifact, field: str, message: str) -> Finding:
    lines = adr.meta_lines
    return Finding(CHECK, "error", adr.file, lines.get(field, lines.get("status", 1)), message)

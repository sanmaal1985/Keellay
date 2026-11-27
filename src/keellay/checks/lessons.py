"""The `lessons` check: a lesson's count matches its occurrences, and a repeated one gets a mechanism or a waiver.

An occurrence is a top-level item under `## Occurrences`; the change it happened in is the first change ID in the
item (`- 2026-04-15, C0019: ...`). A lesson that repeated must be mechanized before that change closes, or the owner
waives the mechanism in the change's Decisions, which then name the lesson by its ID. A last occurrence that names no
change, or a change that is not here or not closed yet, has nothing to check.
"""

import re

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact, FrontMatter
from keellay.checks.markdown import section
from keellay.checks.source import Source

CHECK = "lessons"
_CHANGE_NUMBER = re.compile(r"(?<![A-Za-z0-9])C(\d{4,})(?![0-9])")


def check(artifacts: list[Artifact], source: Source) -> list[Finding]:
    plans: dict[int, Artifact] = {}
    for plan in artifacts:
        number = _number(plan.name_id) if plan.kind == "change" and plan.name_id else None
        if number is not None:
            plans[number] = plan
    findings = []
    for lesson in artifacts:
        if lesson.kind == "lesson" and lesson.meta is not None:
            findings += _check_lesson(lesson, source, plans)
    return findings


def _number(change_id: str) -> int | None:
    match = re.match(r"^C(\d{4,})-", change_id)
    return int(match.group(1)) if match else None


def _value(meta: FrontMatter, name: str) -> str:
    value = meta.get(name)
    return value.strip() if isinstance(value, str) else ""


def _check_lesson(lesson: Artifact, source: Source, plans: dict[int, Artifact]) -> list[Finding]:
    meta, lines = lesson.meta or {}, lesson.meta_lines

    def finding(line: int | None, message: str) -> Finding:
        return Finding(CHECK, "error", lesson.file, line, message)

    findings = []
    status, count = _value(meta, "status"), _value(meta, "count")
    occurrences = section(source.read(lesson.file), "Occurrences")
    items = occurrences.items() if occurrences else []
    if count.isdigit() and int(count) != len(items):
        where = "under Occurrences" if occurrences else "(there is no `## Occurrences` section)"
        findings.append(
            finding(lines.get("count"), f"`count` is {int(count)} but there are {len(items)} occurrences {where}")
        )
    if status == "mechanized" and not _value(meta, "mechanism"):
        findings.append(
            finding(
                lines.get("mechanism", lines.get("status")),
                "the lesson is `mechanized` and `mechanism` is empty; name what enforces the rule",
            )
        )
    if status == "active" and count.isdigit() and int(count) >= 2 and items:
        line, last = items[-1]
        change = _CHANGE_NUMBER.search(last)
        plan = plans.get(int(change.group(1))) if change else None
        if plan is not None and _value(plan.meta or {}, "status") == "closed":
            lesson_id = _value(meta, "id") or lesson.name_id or ""
            decisions = section(source.read(plan.file), "Decisions")
            waived = (
                decisions is not None
                and lesson_id
                and re.search(rf"(?<![A-Za-z0-9]){re.escape(lesson_id)}(?![0-9])", decisions.text())
            )
            if not waived:
                findings.append(
                    finding(
                        line,
                        f"the lesson repeated in change {plan.name_id}, which closed with the "
                        f"lesson still `active` and no waiver for {lesson_id} in its Decisions; "
                        f"mechanize the lesson, or record the owner's waiver in those "
                        f"Decisions by naming {lesson_id}",
                    )
                )
    return findings

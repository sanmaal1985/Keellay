"""Check `front-matter`: every artifact has the fields its format in `method/formats/` requires, with allowed values,
and the number or name in its front matter matches its file or folder name."""

import datetime
import re
from collections.abc import Callable

from keellay.checks import Finding
from keellay.checks.artifacts import Artifact

CHECK = "front-matter"

Rule = Callable[[object], str | None]  # returns what is wrong with the value, or None


def text(value) -> str | None:
    return None if isinstance(value, str) and value.strip() else "must not be empty"


def optional(rule: Rule) -> Rule:
    return lambda value: None if value in ("", None) else rule(value)


def one_of(*allowed: str) -> Rule:
    return lambda value: None if value in allowed else f"is {value!r}; expected one of {', '.join(allowed)}"


def date(value) -> str | None:
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            datetime.date.fromisoformat(value)
            return None
        except ValueError:
            pass
    return f"is {value!r}; expected a date as YYYY-MM-DD"


def number(value) -> str | None:
    return None if isinstance(value, str) and re.fullmatch(r"\d{4}", value) else \
        f"is {value!r}; expected a four-digit number"


def count(value) -> str | None:
    return None if isinstance(value, str) and re.fullmatch(r"\d+", value) else f"is {value!r}; expected a number"


def numbers(value) -> str | None:
    """One four-digit number, or a list of them (`supersedes: [0004, 0007]`)."""
    values = value if isinstance(value, list) else [value]
    return None if values and all(number(item) is None for item in values) else \
        f"is {value!r}; expected a four-digit number or a list of them"


def prd_area(value) -> str | None:
    return None if isinstance(value, str) and re.fullmatch(r"PRD-[a-z0-9]+(?:-[a-z0-9]+)*", value) else \
        f"is {value!r}; expected a PRD area ID such as PRD-limits"


def anything(value) -> str | None:
    return None


# Kind -> field -> rule. Every field listed must be present; `optional` allows an empty value. Fields a format calls
# optional and that may be left out entirely are in OMITTABLE.
SCHEMAS: dict[str, dict[str, Rule]] = {
    "change": {"id": text, "title": text, "path": one_of("change", "feature"),
               "status": one_of("draft", "approved", "in-progress", "review", "closed", "dropped"),
               "approved": optional(date)},
    "idea": {"id": number, "title": text, "status": one_of("new", "assessed", "planned", "done", "declined"),
             "verdict": optional(one_of("go", "clarify", "stop")), "source": one_of("owner", "user", "agent", "retro"),
             "date": date, "prd": optional(prd_area), "change": anything},
    "adr": {"id": number, "title": text, "status": one_of("proposed", "accepted", "superseded"), "date": date,
            "decided-by": text, "supersedes": optional(numbers), "superseded-by": optional(numbers)},
    "lesson": {"id": number, "title": text, "status": one_of("active", "mechanized", "retired"), "count": count,
               "first": date, "last": date, "mechanism": anything},
    "prd": {"product": text, "updated": date},
    "constitution": {"project": text, "updated": date},
    "spec": {"capability": text, "prefix": text},
    "delta": {"capability": text, "prefix": optional(text)},
}
OMITTABLE = {"idea": {"prd"}, "adr": {"supersedes", "superseded-by"}, "delta": {"prefix"}}

# Kind -> the field that must match what the file or folder name says.
NAME_FIELD = {"change": "id", "idea": "id", "adr": "id", "lesson": "id", "spec": "capability", "delta": "capability"}


def check(artifacts: list[Artifact]) -> list[Finding]:
    findings = []
    for artifact in artifacts:
        findings += _check_one(artifact)
    return findings


def _check_one(artifact: Artifact) -> list[Finding]:
    def finding(message: str, line: int | None = 1) -> Finding:
        return Finding(CHECK, "error", artifact.file, line, f"{artifact.kind}: {message}")

    if artifact.error is not None:
        return [finding(str(artifact.error), artifact.error.line)]
    meta, lines = artifact.meta, artifact.meta_lines
    findings = []
    for name, rule in SCHEMAS[artifact.kind].items():
        if name not in meta:
            if name not in OMITTABLE.get(artifact.kind, set()):
                findings.append(finding(f"field `{name}` is missing"))
            continue
        problem = rule(meta[name])
        if problem:
            findings.append(finding(f"`{name}` {problem}", lines.get(name, 1)))
    name_field = NAME_FIELD.get(artifact.kind)
    if name_field is not None:
        if artifact.name_id is None:
            findings.append(finding("the file name must start with the four-digit number, as `0007-topic.md`"))
        elif name_field in meta and meta[name_field] != artifact.name_id:
            findings.append(finding(f"`{name_field}` is {meta[name_field]!r} but the name says {artifact.name_id!r}",
                                    lines.get(name_field, 1)))
    return findings

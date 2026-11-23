"""Check `front-matter`: every artifact has the fields its format in `method/formats/` requires, with allowed values,
and the number or name in its front matter matches its file or folder name."""

import datetime
import re
from collections.abc import Callable

from keellay.checks import Finding
from keellay.checks.artifacts import LETTERS, Artifact

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


def _expected(letter: str, value) -> str:
    """The form a number should have, from what was written: `0012` -> `A0012`, `C0004` -> `A0004`."""
    digits = re.search(r"\d{4}$", value) if isinstance(value, str) else None
    return f"{letter}{digits.group(0)}" if digits else f"{letter}0007"


def number(letter: str) -> Rule:
    """A number of one kind: its letter and four digits (`A0012`)."""
    def rule(value) -> str | None:
        return None if isinstance(value, str) and re.fullmatch(rf"{letter}\d{{4}}", value) else \
            f"is {value!r}; expected a number of the form {_expected(letter, value)}"
    return rule


def numbers(letter: str) -> Rule:
    """One number of one kind, or a list of them (`supersedes: [A0004, A0007]`)."""
    one = number(letter)

    def rule(value) -> str | None:
        values = value if isinstance(value, list) else [value]
        wrong = [item for item in values if one(item) is not None]
        if values and not wrong:
            return None
        example = _expected(letter, wrong[0]) if wrong else f"{letter}0007"
        return f"is {value!r}; expected a number of the form {example}, or a list of them"
    return rule


CHANGE_ID = re.compile(r"C\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*")


def change_id(value) -> str | None:
    """A change ID: its number and topic, as its folder is named (`C0007-session-expiry`)."""
    if isinstance(value, str) and CHANGE_ID.fullmatch(value):
        return None
    head = value.split("-")[0] if isinstance(value, str) else ""
    return f"is {value!r}; expected a change ID of the form {_expected('C', head)}-topic"


def count(value) -> str | None:
    return None if isinstance(value, str) and re.fullmatch(r"\d+", value) else f"is {value!r}; expected a number"


def prd_area(value) -> str | None:
    return None if isinstance(value, str) and re.fullmatch(r"PRD-[a-z0-9]+(?:-[a-z0-9]+)*", value) else \
        f"is {value!r}; expected a PRD area ID such as PRD-limits"


def anything(value) -> str | None:
    return None


# Kind -> field -> rule. Every field listed must be present unless it is in OMITTABLE; `optional` allows an empty
# value. A field the format marks optional, or one that is only set later ("set when assessed", "set when that change
# is approved"), may be left out until it has a value.
SCHEMAS: dict[str, dict[str, Rule]] = {
    "change": {"id": change_id, "title": text, "path": one_of("change", "feature"),
               "status": one_of("draft", "approved", "in-progress", "review", "closed", "dropped"),
               "approved": optional(date)},
    "idea": {"id": number("I"), "title": text, "status": one_of("new", "assessed", "planned", "done", "declined"),
             "verdict": optional(one_of("go", "clarify", "stop")), "source": one_of("owner", "user", "agent", "retro"),
             "date": date, "prd": optional(prd_area), "change": optional(change_id)},
    "adr": {"id": number("A"), "title": text, "status": one_of("proposed", "accepted", "superseded"), "date": date,
            "decided-by": text, "supersedes": optional(numbers("A")), "superseded-by": optional(numbers("A"))},
    "lesson": {"id": number("L"), "title": text, "status": one_of("active", "mechanized", "retired"), "count": count,
               "first": date, "last": date, "mechanism": anything},
    "prd": {"product": text, "updated": date},
    "constitution": {"project": text, "updated": date},
    "spec": {"capability": text, "prefix": text},
    "delta": {"capability": text, "prefix": optional(text)},
}
OMITTABLE = {"change": {"approved"}, "idea": {"verdict", "prd", "change"}, "adr": {"supersedes", "superseded-by"},
             "lesson": {"mechanism"}, "delta": {"prefix"}}

# Kind -> the field that must match what the file or folder name says.
NAME_FIELD = {"change": "id", "idea": "id", "adr": "id", "lesson": "id", "spec": "capability", "delta": "capability"}


def check(artifacts: list[Artifact]) -> list[Finding]:
    findings = []
    for artifact in artifacts:
        findings += _check_one(artifact)
    return findings


def _name_has_number(artifact: Artifact, letter: str) -> bool:
    if artifact.kind == "change":  # the folder name is the change ID
        return bool(CHANGE_ID.fullmatch(artifact.name_id))
    return bool(re.fullmatch(rf"{letter}\d{{4}}", artifact.name_id))


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
    letter = LETTERS.get(artifact.kind)
    if name_field is not None:
        if artifact.name_id is None:
            findings.append(finding(f"the file name must start with the number, as `{letter}0007-topic.md`"))
        elif letter is not None and not _name_has_number(artifact, letter):
            shown = "folder" if artifact.kind == "change" else "file"
            findings.append(finding(f"the {shown} name must start with a number of the form "
                                    f"{_expected(letter, artifact.name_id.split('-')[0])}"))
        elif name_field in meta and meta[name_field] != artifact.name_id:
            findings.append(finding(f"`{name_field}` is {meta[name_field]!r} but the name says {artifact.name_id!r}",
                                    lines.get(name_field, 1)))
    return findings

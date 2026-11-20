"""Make a pull request's title and description a good squash-merge commit message.

The repository squash-merges with the PR title as the commit title and the PR description as the commit body, so
this script fixes both before the merge:

- the title is `<type>: <summary>`, with the type of the branch (`docs/13-architecture` -> `docs`); a title that
  already has that form is kept, otherwise it becomes the only commit's subject or, for several commits, the branch
  topic (`docs/3-artifact-formats` -> `docs: artifact formats`);
- AI attribution lines are removed from the description;
- on a `fix/` branch the description must have the Current, Expected and Unchanged lines (method/formats/bugfix.md);
  they cannot be made up, so their absence is an error.

Run in CI with GH_TOKEN, GITHUB_REPOSITORY and PR_NUMBER set; exits with 1 when something cannot be fixed.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

TYPES = ("feat", "fix", "docs", "ci", "chore", "refactor", "test")
BRANCH = re.compile(r"^(?P<type>[a-z]+)/(?P<rest>.+)$")
TITLE = re.compile(r"^(?P<type>[a-z]+): \S")
ATTRIBUTION = re.compile(r"^\s*Co-Authored-By:\s*Claude|Generated with \[?Claude Code", re.IGNORECASE)
TRIPLE = ("Current", "Expected", "Unchanged")


@dataclass
class Result:
    title: str
    body: str
    errors: list[str] = field(default_factory=list)


def _topic(rest: str) -> str:
    """`13-architecture` -> `architecture`, `0007-session-expiry` -> `session expiry`, `ci-ok` -> `ci ok`."""
    return re.sub(r"^\d+(-|$)", "", rest).replace("-", " ").strip()


def _valid_title(title: str, branch_type: str) -> bool:
    match = TITLE.match(title)
    return bool(match) and match["type"] == branch_type


def fix_message(title: str, body: str | None, branch: str, commit_subjects: list[str]) -> Result:
    """Return the title and description the PR should have, and what cannot be fixed automatically."""
    body = body or ""
    branch_match = BRANCH.match(branch)
    if not branch_match or branch_match["type"] not in TYPES:
        # Not a branch named by the convention (e.g. a bot's branch): leave it alone.
        return Result(title, body)
    branch_type = branch_match["type"]
    result = Result(title.strip(), body)

    if not _valid_title(result.title, branch_type):
        if len(commit_subjects) == 1 and _valid_title(commit_subjects[0].strip(), branch_type):
            result.title = commit_subjects[0].strip()
        elif topic := _topic(branch_match["rest"]):
            result.title = f"{branch_type}: {topic}"
        else:
            result.errors.append(f"cannot derive a title from branch '{branch}'; set it to '{branch_type}: <summary>'")

    lines = [line for line in body.splitlines() if not ATTRIBUTION.search(line)]
    if len(lines) != len(body.splitlines()):
        result.body = "\n".join(lines).strip()

    if branch_type == "fix":
        missing = [name for name in TRIPLE
                   if not re.search(rf"^{name}:\s*\S", result.body, re.MULTILINE)]
        if missing:
            result.errors.append("a fix needs the lines " + ", ".join(f"'{name}: ...'" for name in missing)
                                 + " in the PR description (method/formats/bugfix.md)")
    return result


def _gh(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=True).stdout


def main() -> int:
    repo, number = os.environ["GITHUB_REPOSITORY"], os.environ["PR_NUMBER"]
    pr = json.loads(_gh("api", f"repos/{repo}/pulls/{number}"))
    commits = json.loads(_gh("api", "--paginate", "--slurp", f"repos/{repo}/pulls/{number}/commits"))
    subjects = [c["commit"]["message"].splitlines()[0] for page in commits for c in page]

    result = fix_message(pr["title"], pr["body"], pr["head"]["ref"], subjects)
    changes = {}
    if result.title != pr["title"]:
        changes["title"] = result.title
    if result.body != (pr["body"] or ""):
        changes["body"] = result.body

    if changes:
        if pr["head"]["repo"]["full_name"] != repo:
            # A fork's token cannot edit the PR; say what to change instead.
            result.errors.append(f"set the title to '{result.title}' and remove AI attribution lines")
        else:
            _gh("api", "-X", "PATCH", f"repos/{repo}/pulls/{number}", "--input", "-", stdin=json.dumps(changes))
            print(f"updated the PR ({', '.join(changes)}): title '{result.title}'")
    else:
        print(f"title and description are fine: '{result.title}'")

    for error in result.errors:
        print(f"::error::{error}")
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())

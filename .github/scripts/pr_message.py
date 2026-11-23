"""Make a pull request's title and description a good squash-merge commit message.

The repository squash-merges with the PR title as the commit title and the PR description as the commit body, so
this script fixes both before the merge:

- the title is `<type>: <summary>`, with the type of the branch (`docs/13-architecture` -> `docs`); a title that
  already has that form is kept, otherwise it becomes the subject of the branch's first commit when that has the
  form, else the branch topic (`docs/3-artifact-formats` -> `docs: artifact formats`);
- an empty description is built from the commits: the body of a single commit, or a list of several commits'
  subjects, each with its body indented below it; a description someone wrote is kept;
- AI attribution lines are removed from the description;
- lines longer than 72 characters are wrapped, list items with a hanging indent: GitHub wraps the squash commit body
  at 72 itself, without regard to lists or to lines already wrapped at another width; code blocks, tables and
  headings are left as they are;
- on a `fix/` branch the description must have the Current, Expected and Unchanged lines (method/formats/bugfix.md);
  they cannot be made up, so their absence is an error.

It also checks the PR's commits, on every branch: public commits carry no AI attribution. A commit fails when its
message has an attribution line, or when its author or committer is not a GitHub noreply address (the committer may
also be GitHub itself, for commits made on github.com). The commit's author matters as much as its message: at a
squash merge GitHub turns every commit author other than the merger into a `Co-authored-by` line. Commits cannot be
fixed from here, so this is an error that names each commit.

Before writing, the script reads the PR again and writes nothing when the title or description changed since its
first read: runs overlap, and the run started by that edit handles the newer text.

Run in CI with GH_TOKEN, GITHUB_REPOSITORY and PR_NUMBER set; exits with 1 when something cannot be fixed.
"""

import json
import os
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field

TYPES = ("feat", "fix", "docs", "ci", "chore", "refactor", "test")
BRANCH = re.compile(r"^(?P<type>[a-z]+)/(?P<rest>.+)$")
TITLE = re.compile(r"^(?P<type>[a-z]+): \S")
# Anchored to the start of a line and to the shape of a trailer, so that prose about these lines (and a wrapped
# line that happens to start with their words) is not taken for them: this check blocks merges.
ATTRIBUTION = re.compile(
    r"^\s*Co-Authored-By:\s*Claude\b[^<]*<"              # Co-Authored-By: Claude Opus 5.5 <...>
    r"|^\s*Co-Authored-By:[^<]*<[^>]*@anthropic\.com>"   # any co-author with an Anthropic address
    r"|^\s*Claude-Session:\s*https?://"                  # the session trailer of cloud sessions
    r"|^\W*Generated with \[?Claude Code",               # with or without the leading emoji
    re.IGNORECASE)
ADDRESS = re.compile(r"<[^>]*>")
NOREPLY = re.compile(r"^[^@\s]+@users\.noreply\.github\.com$", re.IGNORECASE)
GITHUB_COMMITTER = "noreply@github.com"  # the committer of commits made on github.com
MAX_COMMITS = 250  # GitHub lists at most this many commits of a pull request
FIX_COMMITS = ("rewrite these commits before the merge: set user.email to your GitHub noreply address "
               "(<id>+<login>@users.noreply.github.com); remove the attribution lines with "
               "git rebase -i origin/main (reword); reset the author with "
               "git rebase origin/main --exec \"git commit --amend --no-edit --reset-author\"; "
               "then push the branch with --force-with-lease")
TRIPLE = ("Current", "Expected", "Unchanged")
WIDTH = 72  # GitHub wraps the squash commit body at this width
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")


@dataclass
class Result:
    title: str
    body: str
    errors: list[str] = field(default_factory=list)


@dataclass
class Commit:
    sha: str
    message: str
    author_email: str
    committer_email: str


def check_commits(commits: list[Commit]) -> list[str]:
    """One error per commit that would put AI attribution into main, then how to fix them; empty when none would.

    No address is printed, not even inside a quoted attribution line: a personal one would only be repeated in a
    public log.
    """
    errors = []
    for commit in commits:
        problems = []
        lines = [ADDRESS.sub("<...>", line.strip()) for line in commit.message.splitlines() if ATTRIBUTION.search(line)]
        if lines:
            problems.append("AI attribution in the message: " + "; ".join(f"'{line}'" for line in lines))
        if not NOREPLY.match(commit.author_email.strip()):
            problems.append("the author is not a GitHub noreply address")
        committer = commit.committer_email.strip()
        if not (NOREPLY.match(committer) or committer.lower() == GITHUB_COMMITTER):
            problems.append("the committer is not a GitHub noreply address")
        if problems:
            subject = commit.message.strip().partition("\n")[0]
            errors.append(f"commit {commit.sha[:7]} '{subject}': " + "; ".join(problems))
    if errors:
        errors.append(FIX_COMMITS)
    if len(commits) >= MAX_COMMITS:
        # GitHub returns no more than MAX_COMMITS, so the ones after them cannot be read: fail rather than pass unseen.
        errors.insert(0, f"the pull request has {MAX_COMMITS} or more commits, and GitHub lists only {MAX_COMMITS}; "
                         "the rest cannot be checked: split the pull request or squash its commits")
    return errors


def _topic(rest: str) -> str:
    """`13-architecture` -> `architecture`, `0007-session-expiry` -> `session expiry`, `ci-ok` -> `ci ok`."""
    return re.sub(r"^\d+(-|$)", "", rest).replace("-", " ").strip()


def _valid_title(title: str, branch_type: str) -> bool:
    match = TITLE.match(title)
    return bool(match) and match["type"] == branch_type


def _without_attribution(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not ATTRIBUTION.search(line)).strip()


def _split(message: str) -> tuple[str, str]:
    """A commit message -> (subject, body without attribution lines)."""
    subject, _, body = message.strip().partition("\n")
    return subject.strip(), _without_attribution(body)


def _body_from_commits(commits: list[tuple[str, str]]) -> str:
    if len(commits) == 1:
        return commits[0][1]
    items = []
    for subject, body in commits:
        indented = "\n".join(f"  {line}" if line else "" for line in body.splitlines())
        items.append(f"- {subject}" + (f"\n{indented}" if indented else ""))
    return "\n".join(items)


def _wrap(text: str) -> str:
    """Wrap lines longer than WIDTH; a list item's continuation lines are indented under its text."""
    lines, in_code = [], False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_code = not in_code
        item = LIST_ITEM.match(line)
        if (in_code or stripped.startswith(("```", "~~~", "|", "#")) or len(line) <= WIDTH
                or (line.startswith(("    ", "\t")) and not item)):
            lines.append(line)
            continue
        if item:
            first, rest, content = item.group(0), " " * len(item.group(0)), line[item.end():]
        else:
            first = rest = line[:len(line) - len(stripped)]
            content = stripped
        lines += textwrap.wrap(content, WIDTH, initial_indent=first, subsequent_indent=rest,
                               break_long_words=False, break_on_hyphens=False)
    return "\n".join(lines)


def fix_message(title: str, body: str | None, branch: str, commit_messages: list[str]) -> Result:
    """Return the title and description the PR should have, and what cannot be fixed automatically.

    `commit_messages` are the full messages of the branch's commits, oldest first.
    """
    body = body or ""
    branch_match = BRANCH.match(branch)
    if not branch_match or branch_match["type"] not in TYPES:
        # Not a branch named by the convention (e.g. a bot's branch): leave it alone.
        return Result(title, body)
    branch_type = branch_match["type"]
    commits = [_split(message) for message in commit_messages]
    result = Result(title.strip(), body)

    if not _valid_title(result.title, branch_type):
        if commits and _valid_title(commits[0][0], branch_type):
            result.title = commits[0][0]
        elif topic := _topic(branch_match["rest"]):
            result.title = f"{branch_type}: {topic}"
        else:
            result.errors.append(f"cannot derive a title from branch '{branch}'; set it to '{branch_type}: <summary>'")

    written = body.replace("\r\n", "\n")  # descriptions written on github.com come with CRLF
    new_body = _wrap(_without_attribution(written) or _body_from_commits(commits))
    if new_body != written.strip():
        result.body = new_body

    if branch_type == "fix":
        missing = [name for name in TRIPLE
                   if not re.search(rf"^\s*{name}:\s*\S", result.body, re.MULTILINE)]
        if missing:
            result.errors.append("a fix needs the lines " + ", ".join(f"'{name}: ...'" for name in missing)
                                 + " in the PR description (method/formats/bugfix.md)")
    return result


def changed_meanwhile(read: dict, latest: dict) -> bool:
    """True when the PR's title or description changed after this run read it.

    Each edit starts its own run, and runs overlap: a run that read the PR before an edit must not write over it, or
    the older text wins. The run started by the edit reads the new text and fixes it.
    """
    return (read["title"], read["body"] or "") != (latest["title"], latest["body"] or "")


def _gh(*args: str, stdin: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, check=True).stdout


def main() -> int:
    repo, number = os.environ["GITHUB_REPOSITORY"], os.environ["PR_NUMBER"]
    pr = json.loads(_gh("api", f"repos/{repo}/pulls/{number}"))
    commits = json.loads(_gh("api", "--paginate", "--slurp", f"repos/{repo}/pulls/{number}/commits"))
    commits = [Commit(c["sha"], c["commit"]["message"], c["commit"]["author"]["email"],
                      c["commit"]["committer"]["email"]) for page in commits for c in page]

    # Before fix_message, which leaves branches outside the naming convention alone: this check holds on every branch.
    commit_errors = check_commits(commits)
    result = fix_message(pr["title"], pr["body"], pr["head"]["ref"], [c.message for c in commits])
    result.errors = commit_errors + result.errors
    changes = {}
    if result.title != pr["title"]:
        changes["title"] = result.title
    if result.body != (pr["body"] or ""):
        changes["body"] = result.body

    if changes:
        latest = json.loads(_gh("api", f"repos/{repo}/pulls/{number}"))
        if changed_meanwhile(pr, latest):
            # The newer run handles the title and description, but the commits are the same: their errors stand, or
            # this run's ci-ok would pass a pull request that the newer run fails.
            print("the title or description changed while this run worked; the run started by that edit fixes it")
            for error in commit_errors:
                print(f"::error::{error}")
            return 1 if commit_errors else 0
        if pr["head"]["repo"]["full_name"] != repo:
            # A fork's token cannot edit the PR; say what to change instead.
            result.errors.append(f"set the title to '{result.title}'; write a description without AI attribution lines")
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

"""Tests for .github/scripts/pr_message.py: the PR title and description become the squash-merge commit message."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "pr_message.py"
_spec = importlib.util.spec_from_file_location("pr_message", _path)
pr_message = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_message)
fix_message = pr_message.fix_message

ATTRIBUTION = (
    "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
    "🤖 Generated with [Claude Code](https://claude.com/claude-code)"
)


# Title


def test_valid_title_is_kept():
    result = fix_message("docs: architecture overview", "x", "docs/13-architecture", ["docs: a", "docs: b"])
    assert result.title == "docs: architecture overview"
    assert result.errors == []


def test_title_comes_from_the_first_commit():
    result = fix_message(
        "Ci/12 pr message",
        "x",
        "ci/12-pr-message",
        ["ci: normalize PR title and description\n\nDetails.", "ci: run on pull requests only"],
    )
    assert result.title == "ci: normalize PR title and description"


def test_type_must_match_the_branch():
    result = fix_message("feat: something", "x", "ci/12-pr-message", ["ci: normalize PR titles", "ci: b"])
    assert result.title == "ci: normalize PR titles"


def test_first_commit_of_another_type_falls_back_to_the_topic():
    result = fix_message("whatever", "x", "docs/C0007-session-expiry", ["feat: session expiry", "docs: b"])
    assert result.title == "docs: session expiry"


def test_branch_with_a_bare_number_still_gives_its_topic():
    result = fix_message("whatever", "x", "docs/0007-session-expiry", ["feat: session expiry", "docs: b"])
    assert result.title == "docs: session expiry"


def test_branch_without_a_topic_is_an_error():
    result = fix_message("whatever", "x", "docs/13", ["chore: a"])
    assert result.errors


def test_branch_outside_the_convention_is_left_alone():
    result = fix_message("Bump uv", "", "dependabot/uv/uv-1.0", ["Bump uv\n\n" + ATTRIBUTION])
    assert (result.title, result.body, result.errors) == ("Bump uv", "", [])
    body = "Bumps uv.\r\n\r\n" + "A line far longer than seventy-two characters that the convention branches wrap. " * 2
    assert fix_message("Bump uv", body, "dependabot/uv/uv-1.0", []).body == body


def test_attribution_is_removed_from_the_description_on_any_branch():
    result = fix_message("Add landing", "Adds the landing.\r\n\r\n" + ATTRIBUTION, "claude/landing-x7Q", [])
    assert (result.title, result.body, result.errors) == ("Add landing", "Adds the landing.", [])


def test_other_line_separators_are_left_alone():
    body = "Release notes. Second line.\fThird."  # noqa: RUF001 - a Unicode line separator on purpose
    assert fix_message("Bump uv", body, "dependabot/uv/uv-1.0", []).body == body


def test_fork_is_told_only_what_would_change(monkeypatch, capsys):
    pr = {
        "title": "Add landing",
        "body": "Adds it.\n\n" + ATTRIBUTION,
        "head": {"ref": "claude/landing-x7Q", "repo": {"full_name": "someone/fork"}},
    }
    commits = [
        [
            {
                "sha": "0123456789abcdef",
                "commit": {"message": "Add landing", "author": {"email": NOREPLY}, "committer": {"email": NOREPLY}},
            }
        ]
    ]

    def gh(*args, stdin=None):
        assert "PATCH" not in args
        return pr_message.json.dumps(commits if args[-1].endswith("/commits") else pr)

    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("PR_NUMBER", "1")
    monkeypatch.setattr(pr_message, "_gh", gh)
    assert pr_message.main() == 1
    out = capsys.readouterr().out
    assert "set the description to the text below" in out and "Adds it." in out
    assert "set the title" not in out


# Description


def test_written_description_is_kept():
    body = "Why this change.\r\n\r\nWhat it does."
    assert fix_message("docs: a", body, "docs/13-architecture", ["docs: a\n\nCommit body."]).body == body


def test_single_commit_gives_its_body():
    message = "docs: architecture overview\n\nAdds docs/architecture.md.\n\n" + ATTRIBUTION
    result = fix_message("docs: architecture overview", "", "docs/13-architecture", [message])
    assert result.body == "Adds docs/architecture.md."


def test_single_commit_without_a_body_gives_an_empty_description():
    assert fix_message("docs: a", None, "docs/13-architecture", ["docs: a"]).body == ""


def test_several_commits_give_a_list():
    messages = [
        "ci: normalize PR titles\n\nFirst line.\n\nSecond paragraph.\n\n" + ATTRIBUTION,
        "ci: run on pull requests only",
    ]
    result = fix_message("ci: normalize PR titles", "", "ci/12-pr-message", messages)
    assert result.body == (
        "- ci: normalize PR titles\n  First line.\n\n  Second paragraph.\n- ci: run on pull requests only"
    )


def test_attribution_lines_are_removed():
    result = fix_message("docs: overview", "Adds the overview.\n\n" + ATTRIBUTION, "docs/13-architecture", [])
    assert result.body == "Adds the overview."


def test_description_of_only_attribution_is_built_from_commits():
    result = fix_message("docs: a", ATTRIBUTION, "docs/13-architecture", ["docs: a\n\nCommit body."])
    assert result.body == "Commit body."


def test_other_mentions_of_claude_stay():
    body = "Wires the Claude Code adapter."
    assert fix_message("feat: wiring", body, "feat/8-wiring", []).body == body


# Wrapping at 72: GitHub wraps the squash commit body there itself


def _wrapped(body: str) -> str:
    return fix_message("docs: a", body, "docs/13-architecture", []).body


def test_long_paragraph_is_wrapped():
    body = "Every squash commit in main should have a meaningful title and a body, also when a PR is opened by hand."
    assert _wrapped(body) == (
        "Every squash commit in main should have a meaningful title and a body,\nalso when a PR is opened by hand."
    )


def test_list_item_gets_a_hanging_indent():
    body = "- Title: a title that is not `<type>: <summary>` now comes from the branch's first commit; the branch topic"
    assert _wrapped(body) == (
        "- Title: a title that is not `<type>: <summary>` now comes from the\n  branch's first commit; the branch topic"
    )


def test_numbered_and_indented_lines_keep_their_indent():
    body = ("1. " + "word " * 20).rstrip() + "\n" + ("  continued " * 8).rstrip()
    for line in _wrapped(body).split("\n")[1:]:
        assert line.startswith(("   ", "  continued"))
    assert all(len(line) <= 72 for line in _wrapped(body).split("\n"))


def test_short_lines_code_tables_and_long_urls_are_left_alone():
    url = "https://github.com/sanmaal1985/Keellay/actions/runs/44693064120/job/136143239307/and/more"
    code = "    " + "x = 1; " * 15
    body = "\n".join(["Short line.", "```", "y = 2; " * 15, "```", "| a | " + "b " * 40 + "|", code, url])
    assert _wrapped(body) == body


def test_wrapped_description_is_not_rewritten_again():
    body = "- Title: a title that is not `<type>: <summary>` now comes from the\r\n  branch's first commit"
    assert _wrapped(body) == body


def test_body_built_from_commits_is_wrapped():
    message = "ci: a\n\n" + "A commit body line wrapped at seventy-two characters by its author ok.\nNext."
    result = fix_message("ci: a", "", "ci/12-wrap", [message, "ci: b"])
    assert all(len(line) <= 72 for line in result.body.split("\n"))


# Fix triple


def test_fix_needs_the_triple():
    result = fix_message("fix: session expiry", "Current: a\nExpected: b", "fix/session-expiry", [])
    assert len(result.errors) == 1
    assert "Unchanged" in result.errors[0]


def test_fix_with_the_triple_passes():
    body = "Current: a\nExpected: b\nUnchanged: c"
    assert fix_message("fix: session expiry", body, "fix/session-expiry", []).errors == []


def test_fix_triple_from_the_commit_counts():
    message = "fix: session expiry\n\nCurrent: a\nExpected: b\nUnchanged: c"
    assert fix_message("fix: session expiry", "", "fix/session-expiry", [message, "fix: test"]).errors == []


def test_session_trailer_is_removed_from_the_description():
    body = "Adds the landing.\n\nClaude-Session: https://claude.ai/code/session_0123"
    assert fix_message("feat: landing", body, "feat/landing", []).body == "Adds the landing."


# Commits: no AI attribution reaches main through a commit's message or its author

check_commits = pr_message.check_commits
Commit = pr_message.Commit
NOREPLY = "12345+someone@users.noreply.github.com"


def _commit(message: str = "ci: a\n\nWhy.", author: str = NOREPLY, committer: str = NOREPLY) -> Commit:
    return Commit("0123456789abcdef", message, author, committer)


def test_clean_commit_passes():
    assert check_commits([_commit()]) == []


def test_commit_made_on_github_passes():
    assert check_commits([_commit(committer="noreply@github.com")]) == []


def test_noreply_address_of_another_contributor_passes():
    assert check_commits([_commit(author="49699333+dependabot[bot]@users.noreply.github.com")]) == []


def test_no_commits_pass():
    assert check_commits([]) == []


def test_ai_agent_accounts_fail_as_author_and_committer():
    for address in (
        "209825114+claude[bot]@users.noreply.github.com",
        "198982749+Copilot@users.noreply.github.com",
        "161369871+google-labs-jules[bot]@users.noreply.github.com",
        "claude[bot]@users.noreply.github.com",
    ):
        errors = check_commits([_commit(author=address, committer=address)])
        assert "the author is the GitHub account of an AI agent" in errors[0], address
        assert "the committer is the GitHub account of an AI agent" in errors[0], address


def test_other_bots_and_logins_that_mention_an_agent_pass():
    for address in (
        "41898282+github-actions[bot]@users.noreply.github.com",
        "12345+claude-fan@users.noreply.github.com",
    ):
        assert check_commits([_commit(author=address)]) == [], address


def test_each_attribution_line_fails():
    for line in (
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>",
        "co-authored-by: claude <noreply@anthropic.com>",
        "Co-authored-by: Assistant <noreply@anthropic.com>",
        "Claude-Session: https://claude.ai/code/session_0123",
        "🤖 Generated with [Claude Code](https://claude.com/claude-code)",
    ):
        errors = check_commits([_commit(f"ci: a\n\nWhy.\n\n{line}")])
        assert errors and line.split("<")[0].strip() in errors[0], line


def test_other_mentions_of_claude_in_a_commit_pass():
    assert check_commits([_commit("feat: Claude Code adapter\n\nWires the Claude Code adapter.")]) == []


def test_prose_about_attribution_lines_passes():
    # A commit that describes these lines, also wrapped so that a line starts with their words.
    message = (
        "fix: strip attribution\n\n"
        "The hook drops 'Generated with Claude Code' lines and the trailers\n"
        "Co-Authored-By: Claude and\n"
        "Claude-Session: and the like, from every commit.\n"
        "'Generated with Claude Code' lines are dropped too.\n"
        "- `Generated with Claude Code`: the line it adds.\n"
        "Generated with Claude Code is the line it adds.\n"
        "Co-Authored-By: Claude lines (with <noreply@anthropic.com>) are dropped."
    )
    assert check_commits([_commit(message)]) == []


def test_co_author_line_naming_an_ai_account_fails():
    message = "ci: a\n\nWhy.\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>"
    errors = check_commits([_commit(message)])
    assert errors and "Co-authored-by: Copilot <...>" in errors[0]
    body = "Why.\n\nCo-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>"
    assert fix_message("ci: a", body, "ci/1-a", []).body == "Why."


def test_co_author_line_naming_a_person_passes():
    assert check_commits([_commit("ci: a\n\nCo-authored-by: Someone <12345+someone@users.noreply.github.com>")]) == []


def test_quoted_attribution_line_hides_the_address():
    errors = check_commits([_commit("ci: a\n\nCo-authored-by: Someone <someone@anthropic.com>")])
    assert "Co-authored-by: Someone <...>" in errors[0]
    assert all("someone@anthropic.com" not in error for error in errors)


def test_anthropic_author_fails():
    errors = check_commits([_commit(author="noreply@anthropic.com")])
    assert "author" in errors[0]


def test_anthropic_committer_fails():
    errors = check_commits([_commit(committer="noreply@anthropic.com")])
    assert "committer" in errors[0]


def test_personal_address_fails_and_is_not_printed():
    errors = check_commits([_commit(author="someone@example.com", committer="someone@example.com")])
    assert "author" in errors[0] and "committer" in errors[0]
    assert all("someone@example.com" not in error for error in errors)


def test_github_address_is_not_an_author():
    assert check_commits([_commit(author="noreply@github.com")])


def test_commit_pushed_by_a_cloud_session_fails():
    # As a cloud session pushed it: trailers in the message, the agent as author, a noreply committer.
    message = (
        "feat: add brand assets and a GitHub Pages landing\n\nAdds the logo.\n\n"
        "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
        "Claude-Session: https://claude.ai/code/session_0123"
    )
    errors = check_commits([_commit(message, author="noreply@anthropic.com")])
    assert errors[0].startswith("commit 0123456 'feat: add brand assets and a GitHub Pages landing': ")
    assert "Co-Authored-By: Claude Opus 5.5" in errors[0] and "Claude-Session:" in errors[0]
    assert "the author is not" in errors[0] and "committer" not in errors[0]
    assert "--reset-author" in errors[-1]


def test_too_many_commits_to_read_fail():
    errors = check_commits([_commit()] * 250)
    assert len(errors) == 1 and "250" in errors[0]
    assert check_commits([_commit()] * 249) == []


def test_only_the_failing_commits_are_named():
    errors = check_commits([_commit(), Commit("fedcba9876543210", "ci: b", "noreply@anthropic.com", NOREPLY)])
    assert len(errors) == 2
    assert errors[0].startswith("commit fedcba9 'ci: b'")


# The check runs in main() on every branch, also outside the naming convention


def test_main_fails_a_branch_outside_the_convention(monkeypatch, capsys):
    pr = {"title": "Bump uv", "body": "", "head": {"ref": "bot/bump-uv", "repo": {"full_name": "o/r"}}}
    commits = [
        [
            {
                "sha": "0123456789abcdef",
                "commit": {
                    "message": "Bump uv\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                    "author": {"email": NOREPLY},
                    "committer": {"email": "noreply@github.com"},
                },
            }
        ]
    ]

    def gh(*args, stdin=None):
        return pr_message.json.dumps(commits if args[-1].endswith("/commits") else pr)

    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("PR_NUMBER", "1")
    monkeypatch.setattr(pr_message, "_gh", gh)
    assert pr_message.main() == 1
    assert "::error::commit 0123456 'Bump uv'" in capsys.readouterr().out


def test_main_keeps_commit_errors_when_the_description_changed_meanwhile(monkeypatch, capsys):
    # The description needs a fix, but the owner edits it while the run works: the newer run handles the text, and
    # this run still fails on the commit.
    reads = iter(
        [
            {"title": "ci: a", "body": "Why.\n\nCo-Authored-By: Claude <noreply@anthropic.com>"},
            {"title": "ci: a", "body": "Why, edited."},
        ]
    )
    commits = [
        [
            {
                "sha": "0123456789abcdef",
                "commit": {
                    "message": "ci: a\n\nCo-Authored-By: Claude <noreply@anthropic.com>",
                    "author": {"email": "noreply@anthropic.com"},
                    "committer": {"email": NOREPLY},
                },
            }
        ]
    ]

    def gh(*args, stdin=None):
        if args[-1].endswith("/commits"):
            return pr_message.json.dumps(commits)
        pr = next(reads)
        pr["head"] = {"ref": "ci/1-a", "repo": {"full_name": "o/r"}}
        return pr_message.json.dumps(pr)

    monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
    monkeypatch.setenv("PR_NUMBER", "1")
    monkeypatch.setattr(pr_message, "_gh", gh)
    assert pr_message.main() == 1
    out = capsys.readouterr().out
    assert "changed while this run worked" in out and "::error::commit 0123456 'ci: a'" in out


# Overlapping runs

changed_meanwhile = pr_message.changed_meanwhile


def test_an_edit_after_the_read_stops_the_write():
    read = {"title": "docs: formats", "body": "old text"}
    latest = {"title": "docs: formats", "body": "new text approved by the owner"}
    assert changed_meanwhile(read, latest)


def test_a_title_edit_after_the_read_stops_the_write():
    assert changed_meanwhile({"title": "docs: a", "body": "x"}, {"title": "docs: b", "body": "x"})


def test_no_edit_lets_the_run_write():
    assert not changed_meanwhile({"title": "docs: a", "body": "x"}, {"title": "docs: a", "body": "x"})


def test_empty_and_missing_body_are_the_same():
    assert not changed_meanwhile({"title": "docs: a", "body": None}, {"title": "docs: a", "body": ""})

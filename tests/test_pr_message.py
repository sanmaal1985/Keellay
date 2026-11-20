"""Tests for .github/scripts/pr_message.py: the PR title and description become the squash-merge commit message."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "pr_message.py"
_spec = importlib.util.spec_from_file_location("pr_message", _path)
pr_message = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_message)
fix_message = pr_message.fix_message

ATTRIBUTION = ("Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
               "🤖 Generated with [Claude Code](https://claude.com/claude-code)")


# Title

def test_valid_title_is_kept():
    result = fix_message("docs: architecture overview", "x", "docs/13-architecture", ["docs: a", "docs: b"])
    assert result.title == "docs: architecture overview"
    assert result.errors == []


def test_title_comes_from_the_first_commit():
    result = fix_message("Ci/12 pr message", "x", "ci/12-pr-message",
                         ["ci: normalize PR title and description\n\nDetails.", "ci: run on pull requests only"])
    assert result.title == "ci: normalize PR title and description"


def test_type_must_match_the_branch():
    result = fix_message("feat: something", "x", "ci/12-pr-message", ["ci: normalize PR titles", "ci: b"])
    assert result.title == "ci: normalize PR titles"


def test_first_commit_of_another_type_falls_back_to_the_topic():
    result = fix_message("whatever", "x", "docs/0007-session-expiry", ["feat: session expiry", "docs: b"])
    assert result.title == "docs: session expiry"


def test_branch_without_a_topic_is_an_error():
    result = fix_message("whatever", "x", "docs/13", ["chore: a"])
    assert result.errors


def test_branch_outside_the_convention_is_left_alone():
    result = fix_message("Bump uv", "", "dependabot/uv/uv-1.0", ["Bump uv\n\n" + ATTRIBUTION])
    assert (result.title, result.body, result.errors) == ("Bump uv", "", [])


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
    messages = ["ci: normalize PR titles\n\nFirst line.\n\nSecond paragraph.\n\n" + ATTRIBUTION,
                "ci: run on pull requests only"]
    result = fix_message("ci: normalize PR titles", "", "ci/12-pr-message", messages)
    assert result.body == ("- ci: normalize PR titles\n"
                           "  First line.\n"
                           "\n"
                           "  Second paragraph.\n"
                           "- ci: run on pull requests only")


def test_attribution_lines_are_removed():
    result = fix_message("docs: overview", "Adds the overview.\n\n" + ATTRIBUTION, "docs/13-architecture", [])
    assert result.body == "Adds the overview."


def test_description_of_only_attribution_is_built_from_commits():
    result = fix_message("docs: a", ATTRIBUTION, "docs/13-architecture", ["docs: a\n\nCommit body."])
    assert result.body == "Commit body."


def test_other_mentions_of_claude_stay():
    body = "Wires the Claude Code adapter."
    assert fix_message("feat: wiring", body, "feat/8-wiring", []).body == body


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

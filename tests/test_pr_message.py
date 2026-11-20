"""Tests for .github/scripts/pr_message.py: the PR title and description become the squash-merge commit message."""

import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "pr_message.py"
_spec = importlib.util.spec_from_file_location("pr_message", _path)
pr_message = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pr_message)
fix_message = pr_message.fix_message


def test_valid_title_is_kept():
    result = fix_message("docs: architecture overview", "", "docs/13-architecture", ["docs: a", "docs: b"])
    assert result.title == "docs: architecture overview"
    assert result.errors == []


def test_single_commit_gives_its_subject():
    result = fix_message("Docs/13 architecture", None, "docs/13-architecture",
                         ["docs: architecture overview as a statement of intent"])
    assert result.title == "docs: architecture overview as a statement of intent"


def test_several_commits_give_the_branch_topic():
    result = fix_message("Docs/3 artifact formats", "", "docs/3-artifact-formats", ["docs: a", "docs: b"])
    assert result.title == "docs: artifact formats"


def test_type_must_match_the_branch():
    result = fix_message("feat: something", "", "ci/ci-ok", ["ci: a", "ci: b"])
    assert result.title == "ci: ci ok"


def test_single_commit_of_another_type_falls_back_to_the_topic():
    result = fix_message("whatever", "", "docs/0007-session-expiry", ["feat: session expiry"])
    assert result.title == "docs: session expiry"


def test_branch_without_a_topic_is_an_error():
    result = fix_message("whatever", "", "docs/13", ["chore: a", "chore: b"])
    assert result.errors


def test_branch_outside_the_convention_is_left_alone():
    result = fix_message("Bump uv", "Co-Authored-By: Claude <x>", "dependabot/uv/uv-1.0", [])
    assert (result.title, result.body, result.errors) == ("Bump uv", "Co-Authored-By: Claude <x>", [])


def test_attribution_lines_are_removed():
    body = ("Adds the overview.\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
            "🤖 Generated with [Claude Code](https://claude.com/claude-code)\n")
    result = fix_message("docs: overview", body, "docs/13-architecture", [])
    assert result.body == "Adds the overview."


def test_other_mentions_of_claude_stay():
    body = "Wires the Claude Code adapter."
    assert fix_message("feat: wiring", body, "feat/8-wiring", []).body == body


def test_fix_needs_the_triple():
    result = fix_message("fix: session expiry", "Current: a\nExpected: b", "fix/session-expiry", [])
    assert len(result.errors) == 1
    assert "Unchanged" in result.errors[0]


def test_fix_with_the_triple_passes():
    body = "Current: a\nExpected: b\nUnchanged: c"
    assert fix_message("fix: session expiry", body, "fix/session-expiry", []).errors == []

"""
tests/test_nodes.py

Unit tests for each LangGraph node function.
All external clients (GitHub, OpenRouter, Slack) are mocked.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from agent.nodes import (
    fetch_diff_node,
    validate_diff_node,
    analyze_code_node,
    score_evaluation_node,
    notify_slack_node,
    finalize_node,
)
from agent.state import ReviewState


# ── Sample state factories ────────────────────────────────────────────────────

def _base_state(**overrides) -> ReviewState:
    """Build a minimal ReviewState for testing."""
    state: ReviewState = {
        "pr_number": 42,
        "repo_owner": "test-org",
        "repo_name": "test-repo",
        "diff_content": "",
        "is_valid_diff": False,
        "review_result": {},
        "risk_score": 0,
        "risk_level": "",
        "should_notify": False,
        "slack_sent": False,
        "github_comment_posted": False,
        "error_message": "",
        "final_status": "",
    }
    state.update(overrides)
    return state


SAMPLE_DIFF = "diff --git a/file.py b/file.py\n+print('hello')\n"

SAMPLE_REVIEW = {
    "risk_score": 75,
    "risk_level": "HIGH",
    "summary": "High risk PR with SQL injection.",
    "security_issues": [
        {
            "owasp_category": "A03:2021 – Injection",
            "severity": "HIGH",
            "title": "SQL Injection",
            "description": "Raw SQL query.",
            "location": "app.py:10",
            "recommendation": "Use ORM.",
        }
    ],
    "quality_issues": [],
    "positive_observations": ["Has docstrings."],
    "merge_recommendation": "REQUEST_CHANGES",
}


# ── Tests: fetch_diff_node ────────────────────────────────────────────────────

class TestFetchDiffNode:
    def test_returns_diff_on_success(self):
        """fetch_diff_node should return diff_content on successful API call."""
        state = _base_state()
        mock_client = MagicMock()
        mock_client.get_pr_diff.return_value = SAMPLE_DIFF

        with patch("agent.nodes.GitHubClient", return_value=mock_client):
            result = fetch_diff_node(state)

        assert result["diff_content"] == SAMPLE_DIFF
        assert result["error_message"] == ""

    def test_returns_empty_diff_on_exception(self):
        """fetch_diff_node should return empty diff and error_message on failure."""
        state = _base_state()

        with patch("agent.nodes.GitHubClient", side_effect=Exception("network fail")):
            result = fetch_diff_node(state)

        assert result["diff_content"] == ""
        assert "network fail" in result["error_message"]

    def test_calls_get_pr_diff_with_correct_args(self):
        """fetch_diff_node must pass owner, repo, pr_number to the client."""
        state = _base_state(repo_owner="myorg", repo_name="myrepo", pr_number=7)
        mock_client = MagicMock()
        mock_client.get_pr_diff.return_value = "diff"

        with patch("agent.nodes.GitHubClient", return_value=mock_client):
            fetch_diff_node(state)

        mock_client.get_pr_diff.assert_called_once_with(
            owner="myorg", repo="myrepo", pr_number=7
        )


# ── Tests: validate_diff_node ─────────────────────────────────────────────────

class TestValidateDiffNode:
    def test_valid_diff_returns_true(self):
        """Non-empty diff within token budget should set is_valid_diff=True."""
        state = _base_state(diff_content=SAMPLE_DIFF)
        result = validate_diff_node(state)
        assert result["is_valid_diff"] is True

    def test_empty_diff_returns_false(self):
        """Empty diff_content should set is_valid_diff=False."""
        state = _base_state(diff_content="")
        result = validate_diff_node(state)
        assert result["is_valid_diff"] is False

    def test_whitespace_only_diff_returns_false(self):
        """Whitespace-only diff should be treated as empty."""
        state = _base_state(diff_content="   \n\n  ")
        result = validate_diff_node(state)
        assert result["is_valid_diff"] is False

    def test_oversized_diff_is_truncated_not_rejected(self):
        """Diffs exceeding the token limit should be truncated, not rejected."""
        # ~50,000 chars ≈ 12,500 tokens — over the 12,000 limit
        large_diff = "+" + "x" * 50_000
        state = _base_state(diff_content=large_diff)

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.max_diff_tokens = 12000
            result = validate_diff_node(state)

        assert result["is_valid_diff"] is True
        assert len(result["diff_content"]) < len(large_diff)
        assert "truncated" in result["diff_content"]


# ── Tests: analyze_code_node ──────────────────────────────────────────────────

class TestAnalyzeCodeNode:
    def test_returns_parsed_review_on_success(self):
        """analyze_code_node should return a parsed dict from the LLM JSON."""
        state = _base_state(diff_content=SAMPLE_DIFF, is_valid_diff=True)
        mock_client = MagicMock()
        mock_client.complete.return_value = json.dumps(SAMPLE_REVIEW)
        mock_client.last_key_index_used = 1

        with patch("agent.nodes.OpenRouterClient", return_value=mock_client):
            result = analyze_code_node(state)

        assert result["review_result"]["risk_score"] == 75
        assert result["error_message"] == ""

    def test_returns_fallback_on_json_decode_error(self):
        """analyze_code_node should return a fallback review if LLM returns non-JSON."""
        state = _base_state(diff_content=SAMPLE_DIFF, is_valid_diff=True)
        mock_client = MagicMock()
        mock_client.complete.return_value = "not valid json at all"
        mock_client.last_key_index_used = 1

        with patch("agent.nodes.OpenRouterClient", return_value=mock_client):
            result = analyze_code_node(state)

        assert "risk_score" in result["review_result"]
        assert result["review_result"]["risk_score"] == 0
        assert result["error_message"] != ""

    def test_returns_fallback_on_llm_client_exception(self):
        """analyze_code_node should return a fallback review if the LLM call fails."""
        state = _base_state(diff_content=SAMPLE_DIFF, is_valid_diff=True)

        with patch(
            "agent.nodes.OpenRouterClient", side_effect=RuntimeError("all keys failed")
        ):
            result = analyze_code_node(state)

        assert "risk_score" in result["review_result"]
        assert "all keys failed" in result["error_message"]


# ── Tests: score_evaluation_node ─────────────────────────────────────────────

class TestScoreEvaluationNode:
    def test_sets_should_notify_true_at_threshold(self):
        """should_notify should be True when risk_score >= risk_threshold (50)."""
        state = _base_state(review_result={"risk_score": 50, "risk_level": "MEDIUM"})

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.risk_threshold = 50
            result = score_evaluation_node(state)

        assert result["should_notify"] is True
        assert result["risk_score"] == 50

    def test_sets_should_notify_false_below_threshold(self):
        """should_notify should be False when risk_score < risk_threshold."""
        state = _base_state(review_result={"risk_score": 25, "risk_level": "LOW"})

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.risk_threshold = 50
            result = score_evaluation_node(state)

        assert result["should_notify"] is False

    def test_extracts_risk_level(self):
        """score_evaluation_node should propagate risk_level from review_result."""
        state = _base_state(
            review_result={"risk_score": 80, "risk_level": "CRITICAL"}
        )

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.risk_threshold = 50
            result = score_evaluation_node(state)

        assert result["risk_level"] == "CRITICAL"


# ── Tests: notify_slack_node ──────────────────────────────────────────────────

class TestNotifySlackNode:
    def test_returns_slack_sent_true_on_success(self):
        """notify_slack_node should return slack_sent=True when Slack succeeds."""
        state = _base_state(
            review_result=SAMPLE_REVIEW,
            should_notify=True,
        )
        mock_client = MagicMock()
        mock_client.send_review_alert.return_value = True

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"
            with patch("agent.nodes.SlackClient", return_value=mock_client):
                result = notify_slack_node(state)

        assert result["slack_sent"] is True

    def test_returns_slack_sent_false_when_webhook_missing(self):
        """notify_slack_node should skip and return False if SLACK_WEBHOOK_URL unset."""
        state = _base_state(review_result=SAMPLE_REVIEW)

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.slack_webhook_url = ""
            result = notify_slack_node(state)

        assert result["slack_sent"] is False

    def test_returns_slack_sent_false_on_client_exception(self):
        """notify_slack_node should return slack_sent=False on SlackClient failure."""
        state = _base_state(review_result=SAMPLE_REVIEW)

        with patch("agent.nodes.settings") as mock_settings:
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"
            with patch("agent.nodes.SlackClient", side_effect=Exception("boom")):
                result = notify_slack_node(state)

        assert result["slack_sent"] is False


# ── Tests: finalize_node ──────────────────────────────────────────────────────

class TestFinalizeNode:
    def test_returns_success_status_on_valid_review(self):
        """finalize_node should return final_status=SUCCESS on clean run."""
        state = _base_state(
            review_result=SAMPLE_REVIEW,
            is_valid_diff=True,
            risk_score=75,
            risk_level="HIGH",
        )
        mock_client = MagicMock()
        mock_client.post_pr_comment.return_value = True

        with patch("agent.nodes.GitHubClient", return_value=mock_client):
            result = finalize_node(state)

        assert result["final_status"] == "SUCCESS"
        assert result["github_comment_posted"] is True

    def test_returns_skipped_when_diff_invalid(self):
        """finalize_node should return final_status=SKIPPED for invalid diff."""
        state = _base_state(
            is_valid_diff=False,
            error_message="Diff is empty.",
        )
        mock_client = MagicMock()
        mock_client.post_pr_comment.return_value = False

        with patch("agent.nodes.GitHubClient", return_value=mock_client):
            result = finalize_node(state)

        assert result["final_status"] == "SKIPPED"

    def test_posts_comment_with_correct_pr_context(self):
        """finalize_node must call post_pr_comment with the correct PR coordinates."""
        state = _base_state(
            repo_owner="myorg",
            repo_name="myrepo",
            pr_number=77,
            review_result=SAMPLE_REVIEW,
        )
        mock_client = MagicMock()
        mock_client.post_pr_comment.return_value = True

        with patch("agent.nodes.GitHubClient", return_value=mock_client):
            finalize_node(state)

        mock_client.post_pr_comment.assert_called_once()
        _, kwargs = mock_client.post_pr_comment.call_args if mock_client.post_pr_comment.call_args else ([], {})
        call_args = mock_client.post_pr_comment.call_args[1]
        assert call_args["owner"] == "myorg"
        assert call_args["repo"] == "myrepo"
        assert call_args["pr_number"] == 77

    def test_handles_github_client_exception_gracefully(self):
        """finalize_node should not raise even if GitHubClient fails."""
        state = _base_state(review_result=SAMPLE_REVIEW)

        with patch("agent.nodes.GitHubClient", side_effect=Exception("auth error")):
            result = finalize_node(state)

        assert result["github_comment_posted"] is False

"""
tests/test_graph.py

Integration tests for the full LangGraph review pipeline.
All external I/O (GitHub, OpenRouter, Slack) is mocked so tests run offline.
"""

import json
import pytest
from unittest.mock import MagicMock, patch

from agent.graph import build_graph, review_graph
from agent.state import ReviewState


# ── Shared fixtures ───────────────────────────────────────────────────────────

SAMPLE_DIFF = """\
diff --git a/app/views.py b/app/views.py
index abc1234..def5678 100644
--- a/app/views.py
+++ b/app/views.py
@@ -5,4 +5,7 @@ from django.http import HttpResponse
+def login(request):
+    query = f"SELECT * FROM users WHERE name='{request.POST['username']}'"
+    cursor.execute(query)
"""

HIGH_RISK_REVIEW = {
    "risk_score": 80,
    "risk_level": "CRITICAL",
    "summary": "SQL injection vulnerability detected.",
    "security_issues": [
        {
            "owasp_category": "A03:2021 – Injection",
            "severity": "CRITICAL",
            "title": "SQL Injection",
            "description": "User input directly interpolated into SQL query.",
            "location": "app/views.py:8",
            "recommendation": "Use parameterised queries or an ORM.",
        }
    ],
    "quality_issues": [],
    "positive_observations": ["New feature is isolated in its own function."],
    "merge_recommendation": "BLOCK",
}

LOW_RISK_REVIEW = {
    "risk_score": 15,
    "risk_level": "LOW",
    "summary": "Minor style improvement. Safe to merge.",
    "security_issues": [],
    "quality_issues": [],
    "positive_observations": ["Clean, readable change."],
    "merge_recommendation": "APPROVE",
}


def _initial_state(**overrides) -> ReviewState:
    """Return a fully populated initial ReviewState for graph invocation."""
    base: ReviewState = {
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
    base.update(overrides)
    return base


# ── Patch helpers ─────────────────────────────────────────────────────────────

def _patch_github_diff(diff: str):
    """Context manager: mock GitHubClient.get_pr_diff to return given diff."""
    mock = MagicMock()
    mock.get_pr_diff.return_value = diff
    mock.post_pr_comment.return_value = True
    return patch("agent.nodes.GitHubClient", return_value=mock)


def _patch_llm(review: dict):
    """Context manager: mock OpenRouterClient.complete to return given review as JSON."""
    mock = MagicMock()
    mock.complete.return_value = json.dumps(review)
    mock.last_key_index_used = 1
    return patch("agent.nodes.OpenRouterClient", return_value=mock)


def _patch_slack(sent: bool = True):
    """Context manager: mock SlackClient.send_review_alert."""
    mock = MagicMock()
    mock.send_review_alert.return_value = sent
    return patch("agent.nodes.SlackClient", return_value=mock)


# ── Tests: happy path (high risk, Slack triggered) ────────────────────────────

class TestGraphHighRiskPath:
    """Full pipeline where a high-risk diff triggers Slack notification."""

    def test_final_status_success_on_high_risk(self):
        """Graph should complete with SUCCESS for a high-risk, valid PR."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(HIGH_RISK_REVIEW),
            _patch_slack(True),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"

            result = review_graph.invoke(_initial_state())

        assert result["final_status"] == "SUCCESS"

    def test_risk_score_propagated_correctly(self):
        """Graph should capture the LLM risk_score in final state."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(HIGH_RISK_REVIEW),
            _patch_slack(True),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"

            result = review_graph.invoke(_initial_state())

        assert result["risk_score"] == 80
        assert result["risk_level"] == "CRITICAL"

    def test_slack_sent_true_for_high_risk(self):
        """Slack notification should be sent when risk_score >= threshold."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(HIGH_RISK_REVIEW),
            _patch_slack(True),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"

            result = review_graph.invoke(_initial_state())

        assert result["slack_sent"] is True

    def test_github_comment_posted_for_high_risk(self):
        """GitHub PR comment should be posted in the finalize step."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(HIGH_RISK_REVIEW),
            _patch_slack(True),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"

            result = review_graph.invoke(_initial_state())

        assert result["github_comment_posted"] is True


# ── Tests: low risk path (no Slack) ──────────────────────────────────────────

class TestGraphLowRiskPath:
    """Full pipeline where a low-risk diff skips Slack notification."""

    def test_slack_not_sent_for_low_risk(self):
        """Slack should NOT be triggered when risk_score < threshold."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(LOW_RISK_REVIEW),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = "https://hooks.slack.com/x"

            with patch("agent.nodes.SlackClient") as mock_slack_cls:
                result = review_graph.invoke(_initial_state())

        # SlackClient.send_review_alert should never be called
        if mock_slack_cls.called:
            mock_slack_cls.return_value.send_review_alert.assert_not_called()

        assert result["slack_sent"] is False

    def test_final_status_success_for_low_risk(self):
        """Graph should still complete SUCCESS for a low-risk PR."""
        with (
            _patch_github_diff(SAMPLE_DIFF),
            _patch_llm(LOW_RISK_REVIEW),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = ""

            result = review_graph.invoke(_initial_state())

        assert result["final_status"] == "SUCCESS"


# ── Tests: empty diff (skip path) ────────────────────────────────────────────

class TestGraphEmptyDiffPath:
    """Pipeline should short-circuit gracefully when the PR diff is empty."""

    def test_skipped_status_for_empty_diff(self):
        """Graph should produce final_status=SKIPPED for an empty diff."""
        mock_gh = MagicMock()
        mock_gh.get_pr_diff.return_value = ""
        mock_gh.post_pr_comment.return_value = False

        with (
            patch("agent.nodes.GitHubClient", return_value=mock_gh),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = ""

            result = review_graph.invoke(_initial_state())

        assert result["final_status"] == "SKIPPED"
        assert result["is_valid_diff"] is False

    def test_llm_not_called_for_empty_diff(self):
        """OpenRouterClient should NOT be instantiated when diff is empty."""
        mock_gh = MagicMock()
        mock_gh.get_pr_diff.return_value = ""
        mock_gh.post_pr_comment.return_value = False

        with (
            patch("agent.nodes.GitHubClient", return_value=mock_gh),
            patch("agent.nodes.OpenRouterClient") as mock_llm_cls,
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = ""

            review_graph.invoke(_initial_state())

        mock_llm_cls.assert_not_called()


# ── Tests: GitHub fetch failure ───────────────────────────────────────────────

class TestGraphGitHubFetchFailure:
    """Pipeline should degrade gracefully when GitHub diff fetch fails."""

    def test_skipped_when_github_raises(self):
        """Graph should return SKIPPED if GitHubClient raises on get_pr_diff."""
        mock_gh = MagicMock()
        mock_gh.get_pr_diff.side_effect = Exception("403 Forbidden")
        mock_gh.post_pr_comment.return_value = False

        with (
            patch("agent.nodes.GitHubClient", return_value=mock_gh),
            patch("agent.nodes.settings") as mock_settings,
        ):
            mock_settings.risk_threshold = 50
            mock_settings.max_diff_tokens = 12000
            mock_settings.slack_webhook_url = ""

            result = review_graph.invoke(_initial_state())

        assert result["final_status"] == "SKIPPED"
        assert "403 Forbidden" in result["error_message"]


# ── Tests: graph construction ─────────────────────────────────────────────────

class TestGraphConstruction:
    """Structural tests for the compiled graph."""

    def test_build_graph_returns_compiled_graph(self):
        """build_graph() should return a compiled, invocable LangGraph object."""
        graph = build_graph()
        assert hasattr(graph, "invoke"), "Graph must have an invoke() method"

    def test_review_graph_module_singleton_is_invocable(self):
        """The module-level review_graph singleton must be invocable."""
        assert callable(getattr(review_graph, "invoke", None))

"""
tests/test_slack_client.py

Unit tests for SlackClient: webhook delivery and Block Kit message structure.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.slack_client import SlackClient


# ── Sample data ───────────────────────────────────────────────────────────────

CRITICAL_REVIEW = {
    "risk_score": 85,
    "risk_level": "CRITICAL",
    "summary": "Multiple injection vulnerabilities detected.",
    "merge_recommendation": "BLOCK",
    "security_issues": [
        {
            "owasp_category": "A03:2021 – Injection",
            "severity": "CRITICAL",
            "title": "SQL Injection",
            "description": "User input passed directly to raw SQL query.",
            "location": "app/db.py:42",
            "recommendation": "Use parameterised queries.",
        },
        {
            "owasp_category": "A02:2021 – Cryptographic Failures",
            "severity": "HIGH",
            "title": "Plaintext password storage",
            "description": "Password stored without hashing.",
            "location": "app/models.py:15",
            "recommendation": "Use bcrypt or argon2.",
        },
    ],
    "quality_issues": [],
    "positive_observations": ["Tests are included."],
}

LOW_REVIEW = {
    "risk_score": 10,
    "risk_level": "LOW",
    "summary": "Minor style nits only.",
    "merge_recommendation": "APPROVE",
    "security_issues": [],
    "quality_issues": [],
    "positive_observations": ["Good test coverage.", "Clean code."],
}

PR_URL = "https://github.com/owner/repo/pull/42"


def _make_slack_response(status_code: int, text: str) -> MagicMock:
    """Build a mock requests.Response for Slack webhook calls."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


# ── Tests: webhook delivery ───────────────────────────────────────────────────

class TestSlackClientDelivery:
    """Tests that the webhook is called correctly."""

    def test_returns_true_on_successful_delivery(self):
        """send_review_alert() should return True when Slack responds 'ok'."""
        client = SlackClient(webhook_url="https://hooks.slack.com/fake")
        mock_resp = _make_slack_response(200, "ok")

        with patch("requests.post", return_value=mock_resp):
            result = client.send_review_alert(CRITICAL_REVIEW, PR_URL)

        assert result is True

    def test_returns_false_on_non_ok_response(self):
        """send_review_alert() should return False on unexpected Slack response."""
        client = SlackClient(webhook_url="https://hooks.slack.com/fake")
        mock_resp = _make_slack_response(400, "invalid_payload")

        with patch("requests.post", return_value=mock_resp):
            result = client.send_review_alert(CRITICAL_REVIEW, PR_URL)

        assert result is False

    def test_returns_false_on_network_error(self):
        """send_review_alert() should return False on connection failure."""
        import requests as _req
        client = SlackClient(webhook_url="https://hooks.slack.com/fake")

        with patch("requests.post", side_effect=_req.ConnectionError("no route")):
            result = client.send_review_alert(CRITICAL_REVIEW, PR_URL)

        assert result is False

    def test_raises_value_error_without_webhook_url(self):
        """SlackClient should raise ValueError if no webhook URL is provided."""
        with patch("core.slack_client.settings") as mock_settings:
            mock_settings.slack_webhook_url = ""
            with pytest.raises(ValueError, match="SLACK_WEBHOOK_URL"):
                SlackClient(webhook_url="")


# ── Tests: Block Kit message structure ───────────────────────────────────────

class TestSlackMessageStructure:
    """Tests that the Slack Block Kit payload contains required elements."""

    def _captured_payload(self, review: dict) -> dict:
        """Run send_review_alert and capture the JSON payload sent to Slack."""
        client = SlackClient(webhook_url="https://hooks.slack.com/fake")
        mock_resp = _make_slack_response(200, "ok")
        captured = {}

        def fake_post(url, json=None, **kwargs):
            captured["payload"] = json
            return mock_resp

        with patch("requests.post", side_effect=fake_post):
            client.send_review_alert(review, PR_URL)

        return captured["payload"]

    def test_payload_contains_attachments(self):
        """Payload must use Slack's attachments format for coloured sidebar."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        assert "attachments" in payload
        assert len(payload["attachments"]) == 1

    def test_critical_review_uses_red_color(self):
        """CRITICAL risk level should use a red colour sidebar."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        color = payload["attachments"][0]["color"]
        assert color == "#FF0000"

    def test_low_review_uses_green_color(self):
        """LOW risk level should use a green colour sidebar."""
        payload = self._captured_payload(LOW_REVIEW)
        color = payload["attachments"][0]["color"]
        assert color == "#36A64F"

    def test_payload_contains_risk_score(self):
        """Payload text must mention the risk score."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        assert "85" in payload["text"]

    def test_payload_contains_pr_url(self):
        """Payload must include the PR URL as an accessible link."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        attachment_str = str(payload["attachments"])
        assert PR_URL in attachment_str

    def test_blocks_include_header(self):
        """Block Kit message must contain a header block."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        blocks = payload["attachments"][0]["blocks"]
        header_blocks = [b for b in blocks if b.get("type") == "header"]
        assert len(header_blocks) >= 1

    def test_security_issues_listed_in_blocks(self):
        """Security issues from the review must appear in the Block Kit blocks."""
        payload = self._captured_payload(CRITICAL_REVIEW)
        blocks_text = str(payload["attachments"][0]["blocks"])
        assert "SQL Injection" in blocks_text

    def test_at_most_3_security_issues_shown(self):
        """Only up to 3 security issues should be shown regardless of input count."""
        review_with_many = {
            **CRITICAL_REVIEW,
            "security_issues": [
                {
                    "owasp_category": f"A0{i}:2021",
                    "severity": "HIGH",
                    "title": f"Issue {i}",
                    "description": "desc",
                    "location": f"file.py:{i}",
                    "recommendation": "fix it",
                }
                for i in range(1, 7)
            ],
        }
        payload = self._captured_payload(review_with_many)
        blocks_text = str(payload["attachments"][0]["blocks"])

        shown = sum(1 for i in range(1, 7) if f"Issue {i}" in blocks_text)
        assert shown <= 3

    def test_empty_security_issues_shows_no_issues_found(self):
        """When no security issues found, a positive message should appear."""
        payload = self._captured_payload(LOW_REVIEW)
        blocks_text = str(payload["attachments"][0]["blocks"])
        assert "No security issues detected" in blocks_text

"""
tests/test_github_client.py

Unit tests for GitHubClient: diff fetching and PR comment posting.
All HTTP calls are mocked — no real GitHub API requests are made.
"""

import pytest
from unittest.mock import MagicMock, patch

from core.github_client import GitHubClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_response(status_code: int, content: str | dict = "") -> MagicMock:
    """Build a mock requests.Response with common attributes."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code < 400
    if isinstance(content, dict):
        resp.json.return_value = content
        resp.text = str(content)
    else:
        resp.text = content
        resp.json.side_effect = ValueError("not JSON")

    if not resp.ok:
        http_error = MagicMock()
        http_error.response = resp
        resp.raise_for_status.side_effect = __import__(
            "requests"
        ).HTTPError(response=resp)
    else:
        resp.raise_for_status.return_value = None

    return resp


SAMPLE_DIFF = """\
diff --git a/app/views.py b/app/views.py
index 1a2b3c4..5d6e7f8 100644
--- a/app/views.py
+++ b/app/views.py
@@ -10,6 +10,7 @@ def login(request):
+    password = request.POST.get('password')  # No hashing
"""


# ── Tests: get_pr_diff ────────────────────────────────────────────────────────

class TestGetPrDiff:
    """Tests for the get_pr_diff method."""

    def test_returns_diff_text_on_success(self):
        """get_pr_diff() should return raw diff text on HTTP 200."""
        client = GitHubClient(token="fake-token")
        mock_resp = _make_response(200, SAMPLE_DIFF)

        with patch.object(client._session, "get", return_value=mock_resp):
            diff = client.get_pr_diff("owner", "repo", 42)

        assert diff == SAMPLE_DIFF

    def test_calls_correct_github_url(self):
        """get_pr_diff() must request the correct pulls endpoint."""
        client = GitHubClient(token="fake-token")
        mock_resp = _make_response(200, SAMPLE_DIFF)

        with patch.object(client._session, "get", return_value=mock_resp) as mock_get:
            client.get_pr_diff("myorg", "myrepo", 99)

        called_url = mock_get.call_args[0][0]
        assert "myorg/myrepo/pulls/99" in called_url

    def test_uses_diff_accept_header(self):
        """get_pr_diff() must send the vnd.github.v3.diff Accept header."""
        client = GitHubClient(token="fake-token")
        mock_resp = _make_response(200, SAMPLE_DIFF)

        with patch.object(client._session, "get", return_value=mock_resp) as mock_get:
            client.get_pr_diff("owner", "repo", 1)

        _, kwargs = mock_get.call_args
        assert kwargs["headers"]["Accept"] == "application/vnd.github.v3.diff"

    def test_raises_on_http_error(self):
        """get_pr_diff() should propagate HTTPError on 4xx/5xx responses."""
        import requests as _req
        client = GitHubClient(token="fake-token")
        mock_resp = _make_response(404)

        with patch.object(client._session, "get", return_value=mock_resp):
            with pytest.raises(_req.HTTPError):
                client.get_pr_diff("owner", "repo", 999)

    def test_raises_value_error_without_token(self):
        """GitHubClient should raise ValueError if no token is given."""
        with patch("core.github_client.settings") as mock_settings:
            mock_settings.github_token = ""
            mock_settings.github_api_base = "https://api.github.com"
            with pytest.raises(ValueError, match="GITHUB_TOKEN"):
                GitHubClient(token="")


# ── Tests: post_pr_comment ────────────────────────────────────────────────────

class TestPostPrComment:
    """Tests for the post_pr_comment method."""

    def test_returns_true_on_success(self):
        """post_pr_comment() should return True on HTTP 201."""
        client = GitHubClient(token="fake-token")
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "html_url": "https://github.com/owner/repo/pull/1#issuecomment-123"
        }

        with patch.object(client._session, "post", return_value=mock_resp):
            result = client.post_pr_comment("owner", "repo", 1, "## Review")

        assert result is True

    def test_calls_issues_comments_endpoint(self):
        """post_pr_comment() must POST to the issues comments endpoint."""
        client = GitHubClient(token="fake-token")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"html_url": "https://github.com/..."}

        with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
            client.post_pr_comment("myorg", "myrepo", 7, "body text")

        called_url = mock_post.call_args[0][0]
        assert "myorg/myrepo/issues/7/comments" in called_url

    def test_sends_body_in_payload(self):
        """post_pr_comment() must include the comment body in the JSON payload."""
        client = GitHubClient(token="fake-token")
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"html_url": "url"}

        with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
            client.post_pr_comment("o", "r", 1, "## My Review Comment")

        _, kwargs = mock_post.call_args
        assert kwargs["json"]["body"] == "## My Review Comment"

    def test_returns_false_on_http_error(self):
        """post_pr_comment() should return False if the API rejects the request."""
        import requests as _req
        client = GitHubClient(token="fake-token")

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.raise_for_status.side_effect = _req.HTTPError(response=mock_resp)

        with patch.object(client._session, "post", return_value=mock_resp):
            result = client.post_pr_comment("o", "r", 1, "body")

        assert result is False

    def test_returns_false_on_network_error(self):
        """post_pr_comment() should return False on network exceptions."""
        import requests as _req
        client = GitHubClient(token="fake-token")

        with patch.object(
            client._session, "post", side_effect=_req.ConnectionError("timeout")
        ):
            result = client.post_pr_comment("o", "r", 1, "body")

        assert result is False

"""
tests/test_llm_client.py

Unit tests for OpenRouterClient, focusing on API key rotation behaviour
on HTTP 429 (rate limit) and HTTP 402 (token/credit limit) responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, call

from core.llm_client import OpenRouterClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_RESPONSE_BODY = {
    "choices": [
        {
            "message": {
                "content": '{"risk_score": 30, "risk_level": "MEDIUM"}'
            }
        }
    ]
}


def _make_response(status_code: int, body: dict | str = "") -> MagicMock:
    """Helper that builds a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.ok = status_code < 400
    if isinstance(body, dict):
        resp.json.return_value = body
        resp.text = json.dumps(body)
    else:
        resp.json.side_effect = ValueError("not JSON")
        resp.text = body
    return resp


# ── Tests: successful completion ──────────────────────────────────────────────

class TestOpenRouterClientSuccess:
    """Tests for the happy path — first key succeeds immediately."""

    def test_complete_returns_content_on_success(self):
        """complete() should return the model content string on HTTP 200."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])
        mock_resp = _make_response(200, SAMPLE_RESPONSE_BODY)

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = client.complete("sys", "user")

        assert '"risk_score": 30' in result
        mock_post.assert_called_once()

    def test_complete_strips_markdown_fences(self):
        """complete() should strip ```json ... ``` fences from LLM output."""
        body = {
            "choices": [
                {"message": {"content": "```json\n{\"risk_score\": 10}\n```"}}
            ]
        }
        client = OpenRouterClient(api_keys=["key-1"])
        mock_resp = _make_response(200, body)

        with patch("requests.post", return_value=mock_resp):
            result = client.complete("sys", "user")

        assert result.startswith("{")
        assert "```" not in result

    def test_correct_headers_sent(self):
        """complete() must include Authorization, Content-Type, HTTP-Referer, X-Title."""
        client = OpenRouterClient(api_keys=["my-key"])
        mock_resp = _make_response(200, SAMPLE_RESPONSE_BODY)

        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.complete("sys", "user")

        _, kwargs = mock_post.call_args
        headers = kwargs["headers"]
        assert headers["Authorization"] == "Bearer my-key"
        assert headers["Content-Type"] == "application/json"
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers


# ── Tests: key rotation on HTTP 429 ──────────────────────────────────────────

class TestKeyRotationOn429:
    """Key rotation should trigger silently on HTTP 429 rate limit responses."""

    def test_rotates_to_second_key_on_429(self):
        """When key 1 gets 429, key 2 should be tried and succeed."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        rate_limited = _make_response(429)
        success = _make_response(200, SAMPLE_RESPONSE_BODY)

        with patch("requests.post", side_effect=[rate_limited, success]) as mock_post:
            result = client.complete("sys", "user")

        assert mock_post.call_count == 2
        assert '"risk_score"' in result
        assert client.last_key_index_used == 2

    def test_rotates_through_all_keys_on_repeated_429(self):
        """When keys 1 and 2 get 429, key 3 should be tried and succeed."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        rate_limited = _make_response(429)
        success = _make_response(200, SAMPLE_RESPONSE_BODY)

        with patch("requests.post", side_effect=[rate_limited, rate_limited, success]):
            result = client.complete("sys", "user")

        assert '"risk_score"' in result
        assert client.last_key_index_used == 3


# ── Tests: key rotation on HTTP 402 ──────────────────────────────────────────

class TestKeyRotationOn402:
    """Key rotation should trigger silently on HTTP 402 token/credit limit responses."""

    def test_rotates_to_second_key_on_402(self):
        """When key 1 gets 402, key 2 should be tried and succeed."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        credit_exhausted = _make_response(402)
        success = _make_response(200, SAMPLE_RESPONSE_BODY)

        with patch("requests.post", side_effect=[credit_exhausted, success]) as mock_post:
            result = client.complete("sys", "user")

        assert mock_post.call_count == 2
        assert '"risk_score"' in result

    def test_rotates_through_all_keys_on_mixed_errors(self):
        """Mixed 429 and 402 errors should still rotate through all keys."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        with patch(
            "requests.post",
            side_effect=[
                _make_response(429),
                _make_response(402),
                _make_response(200, SAMPLE_RESPONSE_BODY),
            ],
        ):
            result = client.complete("sys", "user")

        assert '"risk_score"' in result


# ── Tests: all keys failing ───────────────────────────────────────────────────

class TestAllKeysFailing:
    """RuntimeError should be raised if every key fails."""

    def test_raises_runtime_error_when_all_keys_429(self):
        """RuntimeError raised when all keys return 429."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        with patch("requests.post", return_value=_make_response(429)):
            with pytest.raises(RuntimeError, match="All 3 OpenRouter API key"):
                client.complete("sys", "user")

    def test_raises_runtime_error_when_all_keys_402(self):
        """RuntimeError raised when all keys return 402."""
        client = OpenRouterClient(api_keys=["key-1", "key-2", "key-3"])

        with patch("requests.post", return_value=_make_response(402)):
            with pytest.raises(RuntimeError, match="All 3 OpenRouter API key"):
                client.complete("sys", "user")

    def test_raises_runtime_error_on_single_key_failure(self):
        """RuntimeError raised even with only one key that rate-limits."""
        client = OpenRouterClient(api_keys=["only-key"])

        with patch("requests.post", return_value=_make_response(429)):
            with pytest.raises(RuntimeError):
                client.complete("sys", "user")

    def test_raises_value_error_with_no_keys(self):
        """ValueError raised at construction time if no keys are provided."""
        with pytest.raises(ValueError, match="at least one API key"):
            OpenRouterClient(api_keys=[])

    def test_non_retriable_error_does_not_rotate(self):
        """A generic 500 error should also be treated as failure and rotate keys."""
        client = OpenRouterClient(api_keys=["key-1", "key-2"])
        server_error = _make_response(500, "Internal Server Error")

        with patch("requests.post", return_value=server_error):
            with pytest.raises(RuntimeError):
                client.complete("sys", "user")

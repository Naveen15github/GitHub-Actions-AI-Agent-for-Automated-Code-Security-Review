"""
core/llm_client.py

OpenRouter API client with automatic key rotation.
If a key hits a rate limit (HTTP 429) or token limit (HTTP 402), the client
silently promotes to the next key. All three keys failing raises RuntimeError.
"""

import json
import logging
import re
from typing import List

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    HTTP client for the OpenRouter chat completions API.

    Supports up to three API keys with silent round-robin failover on
    HTTP 429 (rate limit) and HTTP 402 (token/credit limit) responses.
    """

    def __init__(self, api_keys: List[str] | None = None) -> None:
        """
        Initialise the client with a list of API keys.

        Args:
            api_keys: Ordered list of OpenRouter API keys. Falls back to
                      settings.openrouter_api_keys if not provided.

        Raises:
            ValueError: If no API keys are available.
        """
        self._api_keys: List[str] = api_keys or settings.openrouter_api_keys
        if not self._api_keys:
            raise ValueError(
                "OpenRouterClient requires at least one API key. "
                "Set OPENROUTER_API_KEY_1 (and optionally _2, _3)."
            )
        self._model: str = settings.openrouter_model
        self._base_url: str = settings.openrouter_base_url
        self._http_referer: str = settings.openrouter_http_referer
        self._app_title: str = settings.openrouter_app_title
        self.last_key_index_used: int = 0

    # ── Public API ────────────────────────────────────────────────────────────

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """
        Send a chat completion request to OpenRouter with automatic key rotation.

        Tries each API key in sequence. Rotates on HTTP 429 or HTTP 402.
        Raises RuntimeError if all keys are exhausted.

        Args:
            system_prompt: The system role message text.
            user_prompt:   The user role message text.

        Returns:
            The raw text content from the model's first choice message,
            with any markdown code fences stripped.

        Raises:
            RuntimeError: If all API keys fail.
        """
        last_error: Exception | None = None

        for index, key in enumerate(self._api_keys):
            self.last_key_index_used = index + 1
            logger.info(
                "Attempting OpenRouter request with key index %d/%d",
                index + 1,
                len(self._api_keys),
            )
            try:
                response = self._post(key, system_prompt, user_prompt)
            except requests.RequestException as exc:
                logger.warning(
                    "Network error with key %d: %s", index + 1, exc
                )
                last_error = exc
                continue

            if response.status_code in (429, 402):
                reason = "rate limit" if response.status_code == 429 else "token/credit limit"
                logger.warning(
                    "Key %d hit %s (HTTP %d) — rotating to next key",
                    index + 1,
                    reason,
                    response.status_code,
                )
                last_error = RuntimeError(
                    f"Key {index + 1} rejected with HTTP {response.status_code}"
                )
                continue

            if not response.ok:
                msg = (
                    f"OpenRouter returned HTTP {response.status_code} "
                    f"with key {index + 1}: {response.text[:300]}"
                )
                logger.error(msg)
                last_error = RuntimeError(msg)
                continue

            # Successful response
            return self._parse_response(response)

        raise RuntimeError(
            f"All {len(self._api_keys)} OpenRouter API key(s) failed. "
            f"Last error: {last_error}"
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _post(
        self, api_key: str, system_prompt: str, user_prompt: str
    ) -> requests.Response:
        """
        Execute a single POST request to the OpenRouter completions endpoint.

        Args:
            api_key:       The API key to use for this request.
            system_prompt: System role content.
            user_prompt:   User role content.

        Returns:
            Raw requests.Response object.
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._http_referer,
            "X-Title": self._app_title,
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,  # Low temperature for deterministic security analysis
        }
        return requests.post(
            self._base_url,
            headers=headers,
            json=payload,
            timeout=120,
        )

    @staticmethod
    def _parse_response(response: requests.Response) -> str:
        """
        Extract the model's text content from a successful API response.

        Strips markdown code fences (```json ... ```) so callers receive
        clean, parseable JSON.

        Args:
            response: A successful requests.Response from OpenRouter.

        Returns:
            Cleaned text content string.

        Raises:
            ValueError: If the response body cannot be decoded as expected.
        """
        try:
            body = response.json()
            raw_content: str = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Unexpected OpenRouter response structure: {response.text[:500]}"
            ) from exc

        # Strip markdown fences: ```json\n...\n``` or ```\n...\n```
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_content.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        return cleaned.strip()

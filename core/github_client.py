"""
core/github_client.py

GitHub REST API client for fetching PR diffs and posting review comments.
All requests use token-based authentication via the GITHUB_TOKEN secret.
"""

import logging
from typing import Optional

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    Thin wrapper around the GitHub REST API for the operations this agent needs:

    1. Fetching the unified diff for a pull request.
    2. Posting a markdown comment to a pull request thread.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """
        Initialise the client with an authentication token.

        Args:
            token: GitHub personal access token or Actions GITHUB_TOKEN.
                   Falls back to settings.github_token if not provided.

        Raises:
            ValueError: If no token is available.
        """
        self._token: str = token or settings.github_token
        if not self._token:
            raise ValueError(
                "GitHubClient requires a GITHUB_TOKEN. "
                "In GitHub Actions this is provided automatically."
            )
        self._base_url: str = settings.github_api_base
        self._session: requests.Session = self._build_session()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Fetch the unified diff for a pull request.

        Uses the `application/vnd.github.v3.diff` Accept header so GitHub
        returns raw diff text rather than JSON.

        Args:
            owner:     Repository owner (GitHub username or org name).
            repo:      Repository name.
            pr_number: Pull request number.

        Returns:
            Raw unified diff string. Empty string on failure.

        Raises:
            requests.HTTPError: On non-2xx responses.
        """
        url = f"{self._base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {"Accept": "application/vnd.github.v3.diff"}
        logger.info("Fetching PR diff from %s", url)

        response = self._session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        diff = response.text
        logger.info(
            "Fetched PR diff: %d bytes (%d lines)",
            len(diff),
            diff.count("\n"),
        )
        return diff

    def post_pr_comment(
        self, owner: str, repo: str, pr_number: int, body: str
    ) -> bool:
        """
        Post a markdown comment to a pull request conversation thread.

        Uses the Issues comments endpoint (PRs are a superset of Issues in
        the GitHub API, so this endpoint works for both).

        Args:
            owner:     Repository owner.
            repo:      Repository name.
            pr_number: Pull request number.
            body:      Markdown-formatted comment body.

        Returns:
            True if the comment was posted successfully, False otherwise.
        """
        url = f"{self._base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": body}
        logger.info("Posting review comment to PR #%d", pr_number)

        try:
            response = self._session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            comment_url = response.json().get("html_url", "")
            logger.info("Comment posted successfully: %s", comment_url)
            return True
        except requests.HTTPError as exc:
            logger.error(
                "Failed to post PR comment (HTTP %d): %s",
                exc.response.status_code if exc.response else 0,
                exc,
            )
            return False
        except requests.RequestException as exc:
            logger.error("Network error posting PR comment: %s", exc)
            return False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_session(self) -> requests.Session:
        """
        Build a pre-configured requests Session with auth and common headers.

        Returns:
            Configured requests.Session instance.
        """
        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        return session

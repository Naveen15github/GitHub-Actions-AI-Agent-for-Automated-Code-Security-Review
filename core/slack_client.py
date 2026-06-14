"""
core/slack_client.py

Slack incoming webhook client.
Sends rich Block Kit notifications when the risk score exceeds the threshold.
"""

import logging
from typing import Any, Dict, List, Optional

import requests

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Colour map for risk levels ────────────────────────────────────────────────
_RISK_COLORS: Dict[str, str] = {
    "CRITICAL": "#FF0000",
    "HIGH": "#FF6B35",
    "MEDIUM": "#FFD700",
    "LOW": "#36A64F",
}

_RISK_EMOJI: Dict[str, str] = {
    "CRITICAL": "🚨",
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

_MERGE_EMOJI: Dict[str, str] = {
    "APPROVE": "✅",
    "REQUEST_CHANGES": "🔶",
    "BLOCK": "🚫",
}


class SlackClient:
    """
    Sends PR review alerts to a Slack channel via an incoming webhook URL.

    Messages use Slack Block Kit for rich formatting with colour-coded sidebars,
    a risk score badge, top security issues, and a merge recommendation.
    """

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        """
        Initialise with a Slack incoming webhook URL.

        Args:
            webhook_url: Full HTTPS webhook URL. Falls back to
                         settings.slack_webhook_url if not provided.

        Raises:
            ValueError: If no webhook URL is available.
        """
        self._webhook_url: str = webhook_url or settings.slack_webhook_url
        if not self._webhook_url:
            raise ValueError(
                "SlackClient requires a SLACK_WEBHOOK_URL. "
                "Create an incoming webhook in your Slack app settings."
            )

    # ── Public API ────────────────────────────────────────────────────────────

    def send_review_alert(
        self, review_result: Dict[str, Any], pr_url: str
    ) -> bool:
        """
        Send a formatted code review alert to Slack.

        The message includes:
        - Colour-coded sidebar (red=CRITICAL/HIGH, yellow=MEDIUM, green=LOW)
        - Risk score and level badge
        - PR link
        - Executive summary
        - Top 3 security issues
        - Merge recommendation

        Args:
            review_result: Parsed JSON dict from the LLM review analysis.
            pr_url:        Full HTML URL of the pull request.

        Returns:
            True if Slack accepted the message (HTTP 200), False otherwise.
        """
        risk_level: str = review_result.get("risk_level", "UNKNOWN")
        risk_score: int = review_result.get("risk_score", 0)
        summary: str = review_result.get("summary", "No summary available.")
        merge_rec: str = review_result.get("merge_recommendation", "REQUEST_CHANGES")
        security_issues: List[Dict] = review_result.get("security_issues", [])

        color = _RISK_COLORS.get(risk_level, "#808080")
        risk_emoji = _RISK_EMOJI.get(risk_level, "⚪")
        merge_emoji = _MERGE_EMOJI.get(merge_rec, "❓")

        payload = self._build_payload(
            risk_level=risk_level,
            risk_score=risk_score,
            risk_emoji=risk_emoji,
            merge_rec=merge_rec,
            merge_emoji=merge_emoji,
            summary=summary,
            security_issues=security_issues[:3],  # Top 3 only
            pr_url=pr_url,
            color=color,
        )

        logger.info(
            "Sending Slack alert for risk level %s (score %d)", risk_level, risk_score
        )

        try:
            response = requests.post(
                self._webhook_url,
                json=payload,
                timeout=15,
            )
            if response.status_code == 200 and response.text == "ok":
                logger.info("Slack notification sent successfully")
                return True
            logger.error(
                "Slack webhook returned unexpected response: HTTP %d — %s",
                response.status_code,
                response.text[:200],
            )
            return False
        except requests.RequestException as exc:
            logger.error("Failed to send Slack notification: %s", exc)
            return False

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_payload(
        self,
        risk_level: str,
        risk_score: int,
        risk_emoji: str,
        merge_rec: str,
        merge_emoji: str,
        summary: str,
        security_issues: List[Dict],
        pr_url: str,
        color: str,
    ) -> Dict[str, Any]:
        """
        Construct the Slack Block Kit message payload.

        Args:
            risk_level:      e.g. "HIGH"
            risk_score:      Integer 0–100
            risk_emoji:      Emoji matching risk level
            merge_rec:       e.g. "BLOCK"
            merge_emoji:     Emoji matching merge recommendation
            summary:         LLM executive summary text
            security_issues: Up to 3 security issue dicts
            pr_url:          HTML PR URL
            color:           Hex colour code for the attachment sidebar

        Returns:
            Dict ready to POST to the Slack webhook endpoint.
        """
        issue_blocks = self._build_issue_blocks(security_issues)

        return {
            "text": f"{risk_emoji} AI Code Review Alert — {risk_level} Risk (Score: {risk_score}/100)",
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        # ── Header ──────────────────────────────────────────
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{risk_emoji} AI Code Review — {risk_level} Risk",
                                "emoji": True,
                            },
                        },
                        # ── Score + PR Link ──────────────────────────────────
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Risk Score:*\n`{risk_score}/100` {risk_emoji}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Merge Recommendation:*\n{merge_emoji} `{merge_rec}`",
                                },
                            ],
                            "accessory": {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "View PR",
                                    "emoji": True,
                                },
                                "url": pr_url,
                                "action_id": "view_pr",
                            },
                        },
                        {"type": "divider"},
                        # ── Summary ──────────────────────────────────────────
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Summary:*\n{summary}",
                            },
                        },
                        # ── Security Issues ──────────────────────────────────
                        *issue_blocks,
                        {"type": "divider"},
                        # ── Footer ───────────────────────────────────────────
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": "🤖 Generated by *GitHub AI Code Reviewer* • Powered by OpenRouter",
                                }
                            ],
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def _build_issue_blocks(security_issues: List[Dict]) -> List[Dict]:
        """
        Build Slack blocks for each security issue.

        Args:
            security_issues: List of security issue dicts (max 3).

        Returns:
            List of Slack Block Kit block dicts.
        """
        if not security_issues:
            return [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *No security issues detected*",
                    },
                }
            ]

        blocks: List[Dict] = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🔐 Top Security Issues ({len(security_issues)} shown):*",
                },
            }
        ]

        severity_emoji_map = {
            "CRITICAL": "🚨",
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🔵",
        }

        for issue in security_issues:
            severity = issue.get("severity", "UNKNOWN")
            sev_emoji = severity_emoji_map.get(severity, "⚪")
            owasp = issue.get("owasp_category", "N/A")
            title = issue.get("title", "Unnamed issue")
            location = issue.get("location", "Unknown location")
            recommendation = issue.get("recommendation", "See description.")

            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"{sev_emoji} *{title}*\n"
                            f"`{owasp}` | 📍 `{location}`\n"
                            f"💡 _{recommendation}_"
                        ),
                    },
                }
            )

        return blocks

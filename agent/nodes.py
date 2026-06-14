"""
agent/nodes.py

LangGraph node functions for the AI code review pipeline.
Each function takes a ReviewState dict and returns a partial state update.

Node execution order:
  fetch_diff_node → validate_diff_node → analyze_code_node
                                       → score_evaluation_node
                                       → [notify_slack_node →] finalize_node
"""

import json
import logging
from typing import Any, Dict

from agent.prompts import SYSTEM_PROMPT, build_user_prompt
from agent.state import ReviewState
from config.settings import settings
from core.github_client import GitHubClient
from core.llm_client import OpenRouterClient
from core.slack_client import SlackClient

logger = logging.getLogger(__name__)


# ── Node 1: Fetch PR diff ─────────────────────────────────────────────────────

def fetch_diff_node(state: ReviewState) -> Dict[str, Any]:
    """
    Fetch the unified diff for the pull request from GitHub.

    Reads PR context (owner, repo, pr_number) from the state and calls the
    GitHub API. On failure, stores an error message and an empty diff so
    validate_diff_node can short-circuit the graph gracefully.

    Args:
        state: Current ReviewState dict.

    Returns:
        Partial state update with diff_content and optionally error_message.
    """
    logger.info(
        "fetch_diff_node: fetching diff for %s/%s PR #%d",
        state["repo_owner"],
        state["repo_name"],
        state["pr_number"],
    )
    try:
        client = GitHubClient()
        diff = client.get_pr_diff(
            owner=state["repo_owner"],
            repo=state["repo_name"],
            pr_number=state["pr_number"],
        )
        logger.info("fetch_diff_node: fetched %d bytes", len(diff))
        return {"diff_content": diff, "error_message": ""}
    except Exception as exc:
        logger.error("fetch_diff_node: failed to fetch diff — %s", exc)
        return {
            "diff_content": "",
            "error_message": f"Failed to fetch PR diff: {exc}",
        }


# ── Node 2: Validate diff ─────────────────────────────────────────────────────

def validate_diff_node(state: ReviewState) -> Dict[str, Any]:
    """
    Validate that the diff is non-empty and within the token budget.

    Approximates token count as (character count / 4) — a rough but practical
    heuristic for English/code text. If the diff is too large, it is truncated
    with a warning rather than rejected outright.

    Args:
        state: Current ReviewState dict (diff_content must be set).

    Returns:
        Partial state update with is_valid_diff flag.
    """
    diff = state.get("diff_content", "")

    if not diff or not diff.strip():
        logger.warning("validate_diff_node: diff is empty or whitespace-only")
        return {
            "is_valid_diff": False,
            "error_message": state.get("error_message")
            or "PR diff is empty — nothing to review.",
        }

    approx_tokens = len(diff) // 4
    logger.info(
        "validate_diff_node: diff ~%d tokens (limit %d)",
        approx_tokens,
        settings.max_diff_tokens,
    )

    if approx_tokens > settings.max_diff_tokens:
        logger.warning(
            "validate_diff_node: diff exceeds token limit (%d > %d); truncating",
            approx_tokens,
            settings.max_diff_tokens,
        )
        # Truncate to budget; character limit = tokens * 4
        char_limit = settings.max_diff_tokens * 4
        truncated = diff[:char_limit]
        truncated += "\n\n[... diff truncated to fit token limit ...]"
        return {"diff_content": truncated, "is_valid_diff": True}

    return {"is_valid_diff": True}


# ── Node 3: Analyze code via LLM ─────────────────────────────────────────────

def analyze_code_node(state: ReviewState) -> Dict[str, Any]:
    """
    Send the diff to the OpenRouter LLM and parse the JSON review result.

    Uses key rotation transparently. If the LLM response cannot be parsed
    as JSON, a fallback error result is stored so downstream nodes degrade
    gracefully rather than crashing.

    Args:
        state: Current ReviewState dict (diff_content, is_valid_diff must be set).

    Returns:
        Partial state update with review_result dict.
    """
    logger.info("analyze_code_node: sending diff to LLM for analysis")
    try:
        client = OpenRouterClient()
        user_prompt = build_user_prompt(state["diff_content"])
        raw_response = client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        logger.info(
            "analyze_code_node: LLM responded (key index %d used)",
            client.last_key_index_used,
        )
        review_result = json.loads(raw_response)
        logger.info(
            "analyze_code_node: parsed review — risk_score=%d risk_level=%s",
            review_result.get("risk_score", -1),
            review_result.get("risk_level", "UNKNOWN"),
        )
        return {"review_result": review_result, "error_message": ""}
    except json.JSONDecodeError as exc:
        logger.error("analyze_code_node: LLM returned non-JSON — %s", exc)
        return {
            "review_result": _fallback_review("LLM returned non-JSON response."),
            "error_message": f"JSON parse error: {exc}",
        }
    except Exception as exc:
        logger.error("analyze_code_node: unexpected error — %s", exc)
        return {
            "review_result": _fallback_review(str(exc)),
            "error_message": str(exc),
        }


# ── Node 4: Score evaluation ──────────────────────────────────────────────────

def score_evaluation_node(state: ReviewState) -> Dict[str, Any]:
    """
    Extract the risk score from the review result and decide if Slack notification is needed.

    Compares risk_score against settings.risk_threshold (default 50).

    Args:
        state: Current ReviewState dict (review_result must be set).

    Returns:
        Partial state update with risk_score, risk_level, and should_notify.
    """
    review = state.get("review_result", {})
    risk_score: int = int(review.get("risk_score", 0))
    risk_level: str = review.get("risk_level", "LOW")
    should_notify: bool = risk_score >= settings.risk_threshold

    logger.info(
        "score_evaluation_node: risk_score=%d risk_level=%s should_notify=%s",
        risk_score,
        risk_level,
        should_notify,
    )
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "should_notify": should_notify,
    }


# ── Node 5: Notify Slack ──────────────────────────────────────────────────────

def notify_slack_node(state: ReviewState) -> Dict[str, Any]:
    """
    Send a rich Slack Block Kit alert for high-risk pull requests.

    Constructs the PR URL from state context and calls SlackClient.
    Falls back gracefully if SLACK_WEBHOOK_URL is not configured.

    Args:
        state: Current ReviewState dict (review_result must be populated).

    Returns:
        Partial state update with slack_sent boolean.
    """
    if not settings.slack_webhook_url:
        logger.warning(
            "notify_slack_node: SLACK_WEBHOOK_URL not set; skipping Slack notification"
        )
        return {"slack_sent": False}

    pr_url = (
        f"https://github.com/{state['repo_owner']}/{state['repo_name']}"
        f"/pull/{state['pr_number']}"
    )
    logger.info("notify_slack_node: sending alert for PR %s", pr_url)

    try:
        client = SlackClient()
        sent = client.send_review_alert(
            review_result=state["review_result"],
            pr_url=pr_url,
        )
        return {"slack_sent": sent}
    except Exception as exc:
        logger.error("notify_slack_node: failed to send Slack alert — %s", exc)
        return {"slack_sent": False}


# ── Node 6: Finalize ──────────────────────────────────────────────────────────

def finalize_node(state: ReviewState) -> Dict[str, Any]:
    """
    Post the review summary as a GitHub PR comment and set the final status.

    Formats a human-readable markdown comment from the review_result and posts
    it via GitHubClient. Logs the overall pipeline outcome.

    Args:
        state: Fully populated ReviewState dict.

    Returns:
        Partial state update with github_comment_posted and final_status.
    """
    logger.info("finalize_node: finalising review pipeline")

    review = state.get("review_result", {})
    comment_body = _format_github_comment(state, review)
    comment_posted = False

    try:
        client = GitHubClient()
        comment_posted = client.post_pr_comment(
            owner=state["repo_owner"],
            repo=state["repo_name"],
            pr_number=state["pr_number"],
            body=comment_body,
        )
    except Exception as exc:
        logger.error("finalize_node: failed to post GitHub comment — %s", exc)

    # Determine overall pipeline outcome
    if state.get("error_message") and not state.get("is_valid_diff", True):
        final_status = "SKIPPED"
    elif state.get("error_message"):
        final_status = "COMPLETED_WITH_ERRORS"
    else:
        final_status = "SUCCESS"

    logger.info(
        "finalize_node: final_status=%s comment_posted=%s slack_sent=%s",
        final_status,
        comment_posted,
        state.get("slack_sent", False),
    )
    return {
        "github_comment_posted": comment_posted,
        "final_status": final_status,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _fallback_review(reason: str) -> Dict[str, Any]:
    """
    Build a minimal review result dict for use when the LLM call fails.

    Args:
        reason: Human-readable explanation of why the fallback was triggered.

    Returns:
        Review result dict with error-state defaults.
    """
    return {
        "risk_score": 0,
        "risk_level": "LOW",
        "summary": f"Review could not be completed: {reason}",
        "security_issues": [],
        "quality_issues": [],
        "positive_observations": ["Automated review was unable to complete."],
        "merge_recommendation": "REQUEST_CHANGES",
    }


def _format_github_comment(
    state: ReviewState, review: Dict[str, Any]
) -> str:
    """
    Format the LLM review result as a markdown GitHub PR comment.

    Args:
        state:  Current ReviewState (for context metadata).
        review: Parsed LLM review result dict.

    Returns:
        Markdown string suitable for posting as a GitHub PR comment.
    """
    if not review or not review.get("risk_level"):
        error_msg = state.get("error_message", "Unknown error")
        return (
            "## 🤖 AI Code Review — Unable to Complete\n\n"
            f"> **Reason:** {error_msg}\n\n"
            "Please review manually or re-trigger the workflow.\n\n"
            "---\n*Powered by GitHub AI Code Reviewer*"
        )

    risk_level = review.get("risk_level", "UNKNOWN")
    risk_score = review.get("risk_score", 0)
    summary = review.get("summary", "")
    merge_rec = review.get("merge_recommendation", "REQUEST_CHANGES")
    security_issues = review.get("security_issues", [])
    quality_issues = review.get("quality_issues", [])
    positive_obs = review.get("positive_observations", [])

    risk_emoji_map = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
    merge_emoji_map = {"APPROVE": "✅", "REQUEST_CHANGES": "🔶", "BLOCK": "🚫"}
    risk_emoji = risk_emoji_map.get(risk_level, "⚪")
    merge_emoji = merge_emoji_map.get(merge_rec, "❓")

    lines = [
        f"## {risk_emoji} AI Code Review — {risk_level} Risk (Score: {risk_score}/100)",
        "",
        f"**Merge Recommendation:** {merge_emoji} `{merge_rec}`",
        "",
        "### 📋 Summary",
        summary,
        "",
    ]

    if security_issues:
        lines += ["### 🔐 Security Issues", ""]
        for i, issue in enumerate(security_issues, 1):
            sev = issue.get("severity", "UNKNOWN")
            lines += [
                f"#### {i}. {issue.get('title', 'Unnamed')} — `{sev}`",
                f"- **OWASP:** {issue.get('owasp_category', 'N/A')}",
                f"- **Location:** `{issue.get('location', 'N/A')}`",
                f"- **Description:** {issue.get('description', '')}",
                f"- **Recommendation:** {issue.get('recommendation', '')}",
                "",
            ]

    if quality_issues:
        lines += ["### 🛠️ Code Quality Issues", ""]
        for i, issue in enumerate(quality_issues, 1):
            sev = issue.get("severity", "UNKNOWN")
            lines += [
                f"#### {i}. {issue.get('title', 'Unnamed')} — `{sev}`",
                f"- **Location:** `{issue.get('location', 'N/A')}`",
                f"- **Description:** {issue.get('description', '')}",
                f"- **Recommendation:** {issue.get('recommendation', '')}",
                "",
            ]

    if positive_obs:
        lines += ["### ✅ Positive Observations", ""]
        for obs in positive_obs:
            lines.append(f"- {obs}")
        lines.append("")

    lines += [
        "---",
        "*🤖 Generated by [GitHub AI Code Reviewer](https://github.com/ai-code-reviewer) "
        "• Powered by OpenRouter*",
    ]

    return "\n".join(lines)

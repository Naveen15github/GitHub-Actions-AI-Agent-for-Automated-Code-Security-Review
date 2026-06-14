"""
agent/graph.py

LangGraph StateGraph definition for the AI code review pipeline.

Graph topology:
  START
    └─► fetch_diff_node
          └─► validate_diff_node
                ├─ [invalid] ──────────────────────► finalize_node ─► END
                └─ [valid] ──► analyze_code_node
                                 └─► score_evaluation_node
                                       ├─ [score >= threshold] ──► notify_slack_node
                                       │                                └─► finalize_node ─► END
                                       └─ [score < threshold] ──────────► finalize_node ─► END

Entry point: python -m agent.graph
"""

import logging
import os
import sys

from langgraph.graph import StateGraph, END

from agent.nodes import (
    analyze_code_node,
    fetch_diff_node,
    finalize_node,
    notify_slack_node,
    score_evaluation_node,
    validate_diff_node,
)
from agent.state import ReviewState
from config.settings import settings

logger = logging.getLogger(__name__)


# ── Conditional edge predicates ───────────────────────────────────────────────

def _route_after_validation(state: ReviewState) -> str:
    """
    Route after validate_diff_node.

    Returns:
        "analyze"  — diff is valid, continue to LLM analysis.
        "finalize" — diff is invalid or empty, skip to finalize.
    """
    if state.get("is_valid_diff", False):
        return "analyze"
    logger.info("Routing to finalize: diff is invalid — %s", state.get("error_message"))
    return "finalize"


def _route_after_scoring(state: ReviewState) -> str:
    """
    Route after score_evaluation_node.

    Returns:
        "notify"   — risk_score >= threshold, send Slack alert first.
        "finalize" — risk_score below threshold, skip directly to finalize.
    """
    if state.get("should_notify", False):
        logger.info(
            "Routing to notify: risk_score=%d >= threshold=%d",
            state.get("risk_score", 0),
            settings.risk_threshold,
        )
        return "notify"
    logger.info(
        "Routing to finalize: risk_score=%d < threshold=%d",
        state.get("risk_score", 0),
        settings.risk_threshold,
    )
    return "finalize"


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Build and compile the LangGraph StateGraph for PR code review.

    Returns:
        Compiled LangGraph graph ready to invoke.
    """
    graph = StateGraph(ReviewState)

    # ── Register nodes ─────────────────────────────────────────────────────
    graph.add_node("fetch_diff", fetch_diff_node)
    graph.add_node("validate_diff", validate_diff_node)
    graph.add_node("analyze_code", analyze_code_node)
    graph.add_node("score_evaluation", score_evaluation_node)
    graph.add_node("notify_slack", notify_slack_node)
    graph.add_node("finalize", finalize_node)

    # ── Linear edges ───────────────────────────────────────────────────────
    graph.set_entry_point("fetch_diff")
    graph.add_edge("fetch_diff", "validate_diff")
    graph.add_edge("analyze_code", "score_evaluation")
    graph.add_edge("notify_slack", "finalize")
    graph.add_edge("finalize", END)

    # ── Conditional edges ──────────────────────────────────────────────────
    graph.add_conditional_edges(
        "validate_diff",
        _route_after_validation,
        {
            "analyze": "analyze_code",
            "finalize": "finalize",
        },
    )
    graph.add_conditional_edges(
        "score_evaluation",
        _route_after_scoring,
        {
            "notify": "notify_slack",
            "finalize": "finalize",
        },
    )

    return graph.compile()


# Module-level compiled graph — imported by tests and __main__
review_graph = build_graph()


# ── CLI entry point ───────────────────────────────────────────────────────────

def _configure_logging() -> None:
    """Configure structured console logging for the agent run."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """
    CLI entry point: python -m agent.graph

    Loads PR context from environment variables (injected by GitHub Actions),
    validates settings, runs the graph, and exits with an appropriate code.
    """
    _configure_logging()
    logger.info("GitHub AI Code Reviewer — starting")

    try:
        settings.validate()
    except ValueError as exc:
        logger.error("Configuration error: %s", exc)
        sys.exit(1)

    initial_state: ReviewState = {
        "pr_number": settings.pr_number,
        "repo_owner": settings.repo_owner,
        "repo_name": settings.repo_name,
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

    logger.info(
        "Running review for %s/%s PR #%d",
        settings.repo_owner,
        settings.repo_name,
        settings.pr_number,
    )

    try:
        result = review_graph.invoke(initial_state)
    except Exception as exc:
        logger.error("Graph execution failed: %s", exc)
        sys.exit(1)

    final_status = result.get("final_status", "UNKNOWN")
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "N/A")

    logger.info(
        "Review complete — status=%s risk=%s(%d) slack_sent=%s comment_posted=%s",
        final_status,
        risk_level,
        risk_score,
        result.get("slack_sent", False),
        result.get("github_comment_posted", False),
    )

    # Exit non-zero on critical issues so the CI job can be marked as failed
    if final_status not in ("SUCCESS", "SKIPPED"):
        sys.exit(1)


if __name__ == "__main__":
    main()

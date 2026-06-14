"""
agent/state.py

Defines the TypedDict state schema shared across all LangGraph nodes.
Every field is explicitly typed so LangGraph can validate transitions.
"""

from typing import TypedDict


class ReviewState(TypedDict):
    """
    Shared mutable state passed between every node in the LangGraph graph.

    Fields are populated progressively as the graph executes:
    - fetch_diff_node  → diff_content
    - validate_diff_node → is_valid_diff
    - analyze_code_node → review_result
    - score_evaluation_node → risk_score, risk_level, should_notify
    - notify_slack_node → slack_sent
    - finalize_node → github_comment_posted, final_status
    """

    pr_number: int
    repo_owner: str
    repo_name: str
    diff_content: str
    is_valid_diff: bool
    review_result: dict
    risk_score: int
    risk_level: str
    should_notify: bool
    slack_sent: bool
    github_comment_posted: bool
    error_message: str
    final_status: str

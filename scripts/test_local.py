"""
scripts/test_local.py

Local end-to-end test runner for the GitHub AI Code Reviewer.

Usage:
  # Run against a real GitHub PR URL:
  python scripts/test_local.py https://github.com/owner/repo/pull/42

  # Run with a hardcoded sample diff (no GitHub token needed):
  python scripts/test_local.py

The script loads .env, optionally fetches a real PR diff, runs the full
LangGraph agent pipeline, and prints a coloured terminal report.
"""

import argparse
import json
import logging
import os
import sys
import re
from pathlib import Path
from typing import Optional

# ── Bootstrap: ensure project root is on sys.path ────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env before importing settings
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    print("✅  Loaded environment variables from .env")
except ImportError:
    print("⚠️   python-dotenv not installed — relying on shell environment")

# ── ANSI colour helpers ───────────────────────────────────────────────────────

_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_GREEN  = "\033[92m"
_CYAN   = "\033[96m"
_WHITE  = "\033[97m"
_GREY   = "\033[90m"


def _colour(text: str, *codes: str) -> str:
    """Wrap text in ANSI escape codes."""
    return "".join(codes) + text + _RESET


def _risk_colour(risk_level: str) -> str:
    """Return the ANSI colour string for a given risk level."""
    mapping = {
        "CRITICAL": _RED + _BOLD,
        "HIGH":     _RED,
        "MEDIUM":   _YELLOW,
        "LOW":      _GREEN,
    }
    return mapping.get(risk_level, _WHITE)


# ── Sample diff used when no PR URL is provided ───────────────────────────────

SAMPLE_DIFF = """\
diff --git a/app/auth.py b/app/auth.py
new file mode 100644
index 0000000..1a2b3c4
--- /dev/null
+++ b/app/auth.py
@@ -0,0 +1,35 @@
+import sqlite3
+import hashlib
+
+SECRET_KEY = "super_secret_hardcoded_key_123"
+DB_PATH = "/var/app/users.db"
+
+def authenticate_user(username, password):
+    \"\"\"Authenticate a user against the database.\"\"\"
+    conn = sqlite3.connect(DB_PATH)
+    cursor = conn.cursor()
+    # WARNING: vulnerable to SQL injection
+    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
+    cursor.execute(query)
+    user = cursor.fetchone()
+    conn.close()
+    return user is not None
+
+def hash_password(password):
+    \"\"\"Hash a password using MD5 (insecure!).\"\"\"
+    return hashlib.md5(password.encode()).hexdigest()
+
+def get_user_data(user_id):
+    \"\"\"Fetch user data — no authorisation check.\"\"\"
+    conn = sqlite3.connect(DB_PATH)
+    cursor = conn.cursor()
+    cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
+    data = cursor.fetchall()
+    conn.close()
+    return data
+
+def reset_password(username, new_password):
+    \"\"\"Reset password without any verification.\"\"\"
+    conn = sqlite3.connect(DB_PATH)
+    cursor = conn.cursor()
+    cursor.execute(f"UPDATE users SET password='{new_password}' WHERE username='{username}'")
+    conn.commit()
+    conn.close()
"""


# ── PR URL parser ─────────────────────────────────────────────────────────────

def _parse_pr_url(url: str) -> tuple[str, str, int]:
    """
    Extract (owner, repo, pr_number) from a GitHub PR URL.

    Args:
        url: Full GitHub PR URL e.g. https://github.com/owner/repo/pull/42

    Returns:
        Tuple of (owner, repo, pr_number)

    Raises:
        ValueError: If the URL does not match the expected pattern.
    """
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip().rstrip("/"))
    if not match:
        raise ValueError(
            f"Cannot parse PR URL: {url!r}\n"
            "Expected format: https://github.com/owner/repo/pull/42"
        )
    owner, repo, pr_num = match.groups()
    return owner, repo, int(pr_num)


# ── Environment injector ──────────────────────────────────────────────────────

def _inject_env(owner: str, repo: str, pr_number: int) -> None:
    """
    Set required environment variables so Settings can load them.

    Args:
        owner:     Repository owner string.
        repo:      Repository name string.
        pr_number: Pull request number integer.
    """
    os.environ["REPO_OWNER"] = owner
    os.environ["REPO_NAME"] = repo
    os.environ["PR_NUMBER"] = str(pr_number)


# ── Terminal report printer ───────────────────────────────────────────────────

def _print_report(result: dict, key_used: Optional[int] = None) -> None:
    """
    Print a formatted colour terminal report of the review result.

    Args:
        result:   Final ReviewState dict from graph.invoke().
        key_used: OpenRouter API key index that handled the LLM call (if known).
    """
    review = result.get("review_result", {})
    risk_score  = result.get("risk_score", 0)
    risk_level  = result.get("risk_level", "N/A")
    final_status = result.get("final_status", "UNKNOWN")
    slack_sent  = result.get("slack_sent", False)
    comment_ok  = result.get("github_comment_posted", False)

    rc = _risk_colour(risk_level)
    width = 70

    print()
    print(_colour("=" * width, _BOLD, _CYAN))
    print(_colour(" 🤖  GitHub AI Code Review — Local Test Run", _BOLD, _CYAN))
    print(_colour("=" * width, _BOLD, _CYAN))

    # ── Pipeline status ──────────────────────────────────────────────────────
    status_colour = _GREEN if final_status == "SUCCESS" else _YELLOW if final_status == "SKIPPED" else _RED
    print(f"\n  Pipeline Status : {_colour(final_status, status_colour, _BOLD)}")
    if key_used:
        print(f"  OpenRouter Key  : {_colour(f'Key #{key_used}', _GREY)} (used for LLM call)")
    print(f"  Slack Sent      : {_colour('✅ Yes', _GREEN) if slack_sent else _colour('⏭  No', _GREY)}")
    print(f"  GitHub Comment  : {_colour('✅ Posted', _GREEN) if comment_ok else _colour('⏭  Skipped', _GREY)}")

    if result.get("error_message"):
        print(f"\n  {_colour('⚠️  Error:', _YELLOW)} {result['error_message']}")

    if not review:
        print(f"\n  {_colour('No review data available (diff was empty or an error occurred).', _GREY)}")
        print()
        return

    # ── Risk score ───────────────────────────────────────────────────────────
    print()
    print(_colour(f"  RISK SCORE: {risk_score}/100  [{risk_level}]", rc, _BOLD))
    print()

    # ── Summary ──────────────────────────────────────────────────────────────
    print(_colour("  SUMMARY", _BOLD, _CYAN))
    summary = review.get("summary", "No summary.")
    for line in _wrap(summary, width - 4):
        print(f"    {line}")
    print()

    # ── Merge recommendation ─────────────────────────────────────────────────
    merge_rec = review.get("merge_recommendation", "N/A")
    merge_colour = _GREEN if merge_rec == "APPROVE" else _YELLOW if merge_rec == "REQUEST_CHANGES" else _RED
    merge_emoji = {"APPROVE": "✅", "REQUEST_CHANGES": "🔶", "BLOCK": "🚫"}.get(merge_rec, "❓")
    print(f"  {_colour('MERGE RECOMMENDATION', _BOLD, _CYAN)}: {_colour(f'{merge_emoji} {merge_rec}', merge_colour, _BOLD)}")
    print()

    # ── Security issues ──────────────────────────────────────────────────────
    sec_issues = review.get("security_issues", [])
    print(_colour(f"  SECURITY ISSUES ({len(sec_issues)} found)", _BOLD, _CYAN))
    if sec_issues:
        for i, issue in enumerate(sec_issues, 1):
            sev = issue.get("severity", "?")
            sev_c = _risk_colour(sev)
            print(f"\n    {i}. {_colour(issue.get('title', 'Untitled'), _BOLD)} [{_colour(sev, sev_c)}]")
            print(f"       OWASP    : {issue.get('owasp_category', 'N/A')}")
            print(f"       Location : {_colour(issue.get('location', 'N/A'), _GREY)}")
            for line in _wrap(f"Desc: {issue.get('description', '')}", width - 12):
                print(f"       {line}")
            for line in _wrap(f"Fix : {issue.get('recommendation', '')}", width - 12):
                print(f"       {_colour(line, _GREEN)}")
    else:
        print(f"    {_colour('✅ No security issues detected', _GREEN)}")
    print()

    # ── Quality issues ────────────────────────────────────────────────────────
    qual_issues = review.get("quality_issues", [])
    print(_colour(f"  CODE QUALITY ISSUES ({len(qual_issues)} found)", _BOLD, _CYAN))
    if qual_issues:
        for i, issue in enumerate(qual_issues, 1):
            sev = issue.get("severity", "?")
            sev_c = _risk_colour(sev)
            print(f"\n    {i}. {_colour(issue.get('title', 'Untitled'), _BOLD)} [{_colour(sev, sev_c)}]")
            print(f"       Location : {_colour(issue.get('location', 'N/A'), _GREY)}")
            for line in _wrap(f"Desc: {issue.get('description', '')}", width - 12):
                print(f"       {line}")
    else:
        print(f"    {_colour('✅ No quality issues detected', _GREEN)}")
    print()

    # ── Positive observations ─────────────────────────────────────────────────
    pos = review.get("positive_observations", [])
    print(_colour("  POSITIVE OBSERVATIONS", _BOLD, _CYAN))
    for obs in pos:
        print(f"    ✅  {obs}")
    print()

    print(_colour("=" * width, _BOLD, _CYAN))
    print()


def _wrap(text: str, width: int) -> list[str]:
    """Naively wrap text at word boundaries for terminal output."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 > width:
            if current:
                lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    return lines or [""]


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Entry point for the local end-to-end test runner.

    Parses CLI arguments, resolves diff source (real PR or sample),
    injects environment, runs the graph, and prints the report.
    """
    logging.basicConfig(
        level=logging.WARNING,   # Suppress verbose INFO logs in local mode
        format="%(levelname)s — %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Run the GitHub AI Code Reviewer locally (end-to-end).",
        epilog="Example: python scripts/test_local.py https://github.com/owner/repo/pull/42",
    )
    parser.add_argument(
        "pr_url",
        nargs="?",
        help="Full GitHub PR URL. Omit to use the built-in sample diff.",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Suppress Slack notification even if SLACK_WEBHOOK_URL is set.",
    )
    parser.add_argument(
        "--no-comment",
        action="store_true",
        help="Skip posting the GitHub PR comment.",
    )
    args = parser.parse_args()

    if args.no_slack:
        os.environ.pop("SLACK_WEBHOOK_URL", None)
        print("⏭   Slack notifications disabled via --no-slack flag")

    use_sample = args.pr_url is None

    if use_sample:
        print("ℹ️   No PR URL provided — using built-in sample diff")
        print("    (The LLM will still run; GitHub API will NOT be called for diff fetch)\n")
        owner, repo, pr_number = "sample-org", "sample-repo", 0
        _inject_env(owner, repo, pr_number)

        # Monkey-patch GitHubClient to bypass real API calls for the sample run
        import agent.nodes as nodes_module
        from core.github_client import GitHubClient

        _real_gh_init = GitHubClient.__init__

        class _SampleGitHubClient(GitHubClient):
            def __init__(self, token=None):
                # Skip token validation for sample run
                import requests as _req
                self._token = token or os.getenv("GITHUB_TOKEN", "sample-token")
                self._base_url = "https://api.github.com"
                self._session = _req.Session()

            def get_pr_diff(self, owner, repo, pr_number):
                print(f"📋  Using built-in sample diff ({len(SAMPLE_DIFF)} bytes)")
                return SAMPLE_DIFF

            def post_pr_comment(self, owner, repo, pr_number, body):
                if args.no_comment:
                    print("⏭   GitHub comment skipped via --no-comment")
                    return False
                print("\n" + "─" * 60)
                print("📝  GitHub PR Comment (preview — not actually posted):")
                print("─" * 60)
                # Print first 800 chars of comment to keep output manageable
                preview = body[:800] + ("…" if len(body) > 800 else "")
                print(preview)
                print("─" * 60 + "\n")
                return True

        nodes_module.GitHubClient = _SampleGitHubClient  # type: ignore[attr-defined]

    else:
        try:
            owner, repo, pr_number = _parse_pr_url(args.pr_url)
        except ValueError as exc:
            print(f"❌  {exc}")
            sys.exit(1)

        print(f"🔍  Reviewing PR #{pr_number} in {owner}/{repo}")
        _inject_env(owner, repo, pr_number)

        # Honour --no-comment by patching post_pr_comment
        if args.no_comment:
            from core.github_client import GitHubClient
            import agent.nodes as nodes_module

            _orig_post = GitHubClient.post_pr_comment

            def _noop_post(self, *a, **kw):
                print("⏭   GitHub comment skipped via --no-comment")
                return False

            GitHubClient.post_pr_comment = _noop_post  # type: ignore[method-assign]

    # ── Validate at least one OpenRouter key is present ───────────────────────
    keys = [
        os.getenv("OPENROUTER_API_KEY_1", ""),
        os.getenv("OPENROUTER_API_KEY_2", ""),
        os.getenv("OPENROUTER_API_KEY_3", ""),
    ]
    if not any(keys):
        print(
            "❌  No OpenRouter API keys found.\n"
            "    Set OPENROUTER_API_KEY_1 (and optionally _2, _3) in your .env file."
        )
        sys.exit(1)

    print("🚀  Running LangGraph agent pipeline...\n")

    # Re-import after env injection so Settings picks up the values
    import importlib
    import config.settings as settings_module
    settings_module.settings = settings_module.Settings()  # reinitialise

    from agent.graph import review_graph

    initial_state: dict = {
        "pr_number": pr_number,
        "repo_owner": owner,
        "repo_name": repo,
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

    try:
        result = review_graph.invoke(initial_state)
    except Exception as exc:
        print(f"\n❌  Agent pipeline raised an exception: {exc}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    _print_report(result)

    # Exit non-zero for CRITICAL/HIGH so CI pipelines can act on it
    exit_code = 0
    if result.get("risk_level") in ("CRITICAL", "HIGH"):
        exit_code = 2
    elif result.get("final_status") not in ("SUCCESS", "SKIPPED"):
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

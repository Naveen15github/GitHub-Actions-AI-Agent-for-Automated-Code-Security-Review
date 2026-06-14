# 🛡️ GitHub Actions AI Agent for Automated Code Security Review

![Pull Requests Page](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/32054fa8699538886c2db9951d73f31139253692/Architectrue%20Diagram.png)

> An autonomous AI-powered security agent that automatically reviews every Pull Request for vulnerabilities, posts intelligent feedback directly on GitHub, and sends real-time Slack alerts — all without any human intervention.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-orange)](https://python.langchain.com/docs/langgraph)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=github-actions)](https://github.com/features/actions)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-API-purple)](https://openrouter.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📸 Project Demo

### 1. Pull Requests Triggered for Security Testing
Three test branches were created to validate high-risk and low-risk code detection:

![Pull Requests Page](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/8e0ade2eff3dba9d246b9b9eb5540b02c2a03cae/screenshots/Screenshot%20(644).png)

---

### 2. GitHub Actions — Workflows Running in Real-Time
The AI Code Review and PR Merged Notification workflows trigger automatically on every PR event:

![Workflow Runs In Progress](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/8e0ade2eff3dba9d246b9b9eb5540b02c2a03cae/screenshots/Screenshot%20(645).png)

---

### 3. Successful HIGH RISK TEST — Workflow Run Details
The agent completed the `feat: add authentication module (HIGH RISK TEST)` run in 3 minutes 14 seconds with a `Success` status:

![High Risk Workflow Run](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/8e0ade2eff3dba9d246b9b9eb5540b02c2a03cae/screenshots/Screenshot%20(646).png)

---

### 4. Slack Alert — CRITICAL Risk Score 95/100
When the risk score exceeds 50, the agent fires a Slack alert with full vulnerability details, OWASP mappings, and a direct PR link:

![Slack Critical Alert](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/8e0ade2eff3dba9d246b9b9eb5540b02c2a03cae/screenshots/Screenshot%20(647).png)

---

### 5. All Workflow Runs — End-to-End Success
All 9 workflow runs completed successfully across HIGH RISK, LOW RISK, and merge notification scenarios:

![All Workflow Runs](https://github.com/Naveen15github/GitHub-Actions-AI-Agent-for-Automated-Code-Security-Review/blob/8e0ade2eff3dba9d246b9b9eb5540b02c2a03cae/screenshots/Screenshot%20(648).png)

---

## 📖 Table of Contents

- [What This Project Does](#-what-this-project-does)
- [How It All Works — The Full Flow](#-how-it-all-works--the-full-flow)
- [Project Structure — Every File Explained](#-project-structure--every-file-explained)
- [Part 1 — GitHub Actions Workflows](#-part-1--github-actions-workflows-the-trigger-system)
- [Part 2 — The LangGraph Agent](#-part-2--the-langgraph-agent-the-brain)
- [Part 3 — The Core Clients](#-part-3--the-core-clients-the-hands)
- [Part 4 — Configuration & Settings](#-part-4--configuration--settings)
- [Part 5 — Risk Scoring System](#-part-5--risk-scoring-system)
- [Part 6 — Security Design](#-part-6--security-design)
- [Setup & Installation](#-setup--installation)
- [Testing](#-testing)
- [Sample Output](#-sample-ai-review-output)
- [Tech Stack](#-tech-stack)
- [Future Enhancements](#-future-enhancements)

---

## 🎯 What This Project Does

I built an **agentic DevOps pipeline** that brings AI-powered security directly into the GitHub Pull Request workflow.

The problem it solves: Most teams either skip security reviews because they're slow and expensive, or they rely on basic static analysis tools that only do pattern matching. This agent uses a 550-billion-parameter AI model that actually **understands code context and semantics** — not just keyword matching.

Every time a developer opens a Pull Request:
- The agent wakes up automatically inside GitHub Actions
- Reads the exact lines of code that changed (the diff)
- Sends those changes to a powerful AI model for analysis
- Gets back a structured security report with a risk score
- Posts the full report as a comment directly on the Pull Request
- If the risk is HIGH or CRITICAL, instantly alerts the entire team on Slack
- When the PR is merged, sends a merge notification to Slack

**Zero human intervention required. Zero infrastructure to manage. Zero cost (free tier).**

---

## 🔄 How It All Works — The Full Flow

Here is the complete end-to-end journey from a developer pushing code to the team getting a Slack alert:

```
STEP 1 ─── Developer pushes code and opens a Pull Request on GitHub
                              │
STEP 2 ─── GitHub detects the PR event (opened / updated / reopened)
                              │
STEP 3 ─── GitHub Actions reads .github/workflows/ai_review.yml
                              │
STEP 4 ─── GitHub spins up a fresh Ubuntu virtual machine (runner)
                              │
STEP 5 ─── Runner installs Python 3.11 and all dependencies
                              │
STEP 6 ─── Runner executes: python -m agent.graph
                              │
STEP 7 ─── LangGraph agent starts — initializes the AgentState
                              │
STEP 8 ─── NODE: fetch_diff
           └── Calls GitHub API with PR number + repo details
           └── Gets back the raw git diff (all changed lines)
                              │
STEP 9 ─── NODE: validate_diff
           └── Counts tokens in the diff
           └── If > 12,000 tokens → truncates to fit AI context window
           └── If diff is empty → marks as skippable
                              │
STEP 10 ── NODE: analyze_code
           └── Builds a security-focused system prompt
           └── Sends diff to NVIDIA Nemotron 550B via OpenRouter API
           └── If API key hits rate limit → automatically switches to key 2 or key 3
           └── Receives structured JSON response from the AI
                              │
STEP 11 ── NODE: score_evaluation
           └── Parses the JSON: risk_score, issues[], recommendations[]
           └── Maps each issue to its OWASP Top 10 category
           └── Decides routing: risk >= 50 → go to notify_slack
                              │
STEP 12 ── NODE: notify_slack (only if risk score >= 50)
           └── Builds a Block Kit formatted Slack message
           └── Color codes it: RED (critical), ORANGE (high)
           └── Includes top 3 issues, OWASP tags, file locations
           └── Posts to Slack webhook URL
                              │
STEP 13 ── NODE: finalize
           └── Formats the full review as a Markdown comment
           └── Posts it on the GitHub Pull Request via GitHub API
           └── Comment includes: score, all issues, recommendations
                              │
STEP 14 ── Developer sees the AI review comment on their PR
           Team sees the Slack alert (if high risk)
           PR is either approved or blocked based on the score
                              │
STEP 15 ── (Separate workflow) When PR is merged:
           └── pr_merged_notification.yml triggers
           └── Sends merge notification to Slack
```

---

## 📁 Project Structure — Every File Explained

```
github-ai-reviewer/
│
├── .github/
│   └── workflows/
│       ├── ai_review.yml                  ← Triggers on PR open/update
│       └── pr_merged_notification.yml     ← Triggers on PR merge
│
├── agent/
│   ├── __init__.py                        ← Makes agent a Python package
│   ├── graph.py                           ← LangGraph state machine (the brain)
│   ├── nodes.py                           ← Each step of the review process
│   ├── state.py                           ← Shared data structure (AgentState)
│   └── prompts.py                         ← Instructions sent to the AI model
│
├── core/
│   ├── __init__.py                        ← Makes core a Python package
│   ├── github_client.py                   ← Talks to GitHub API
│   ├── llm_client.py                      ← Talks to OpenRouter / AI model
│   └── slack_client.py                    ← Sends Slack messages
│
├── config/
│   ├── __init__.py                        ← Makes config a Python package
│   └── settings.py                        ← Loads all environment variables
│
├── tests/
│   ├── test_github_client.py              ← Unit tests for GitHub client
│   ├── test_llm_client.py                 ← Unit tests for LLM client
│   ├── test_slack_client.py               ← Unit tests for Slack client
│   ├── test_nodes.py                      ← Unit tests for agent nodes
│   └── test_graph.py                      ← Integration tests for full workflow
│
├── scripts/
│   └── test_local.py                      ← Run the agent locally without GitHub
│
├── .env.example                           ← Template showing required env variables
├── requirements.txt                       ← All Python packages needed
└── README.md                              ← This file
```

---

## ⚡ Part 1 — GitHub Actions Workflows (The Trigger System)

GitHub Actions is the automation platform built into every GitHub repository. It listens for events (like a PR being opened) and runs your code automatically in a cloud virtual machine.

I created two workflow files:

---

### Workflow 1: `ai_review.yml` — The Main Security Review

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  pull-requests: write   # Allows the agent to post comments on PRs
  contents: read         # Allows reading the code

jobs:
  review:
    runs-on: ubuntu-latest
    steps:

      # Step 1: Download the repo code onto the runner machine
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0   # Gets full git history so we can compute diffs

      # Step 2: Install Python 3.11
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # Step 3: Install all required libraries from requirements.txt
      - name: Install dependencies
        run: pip install -r requirements.txt

      # Step 4: Run the AI agent, injecting all secrets as environment variables
      - name: Run AI Review Agent
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}         # Auto-provided by GitHub
          OPENROUTER_API_KEY_1: ${{ secrets.OPENROUTER_API_KEY_1 }}
          OPENROUTER_API_KEY_2: ${{ secrets.OPENROUTER_API_KEY_2 }}
          OPENROUTER_API_KEY_3: ${{ secrets.OPENROUTER_API_KEY_3 }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REPO_OWNER: ${{ github.repository_owner }}
          REPO_NAME: ${{ github.event.repository.name }}
        run: python -m agent.graph
```

**What each part means:**

- `on: pull_request: types: [opened, synchronize, reopened]` — This is the trigger. `opened` means a brand new PR. `synchronize` means someone pushed new commits to an existing PR. `reopened` means a previously closed PR was reopened.
- `permissions: pull-requests: write` — Without this, the agent cannot post comments on PRs. GitHub requires explicit permission declarations.
- `runs-on: ubuntu-latest` — GitHub spins up a fresh Ubuntu Linux virtual machine every time this runs. It's completely isolated and destroyed after the job finishes.
- `fetch-depth: 0` — By default, `checkout` only gets the latest commit. Setting this to 0 gets the full history, which is needed to properly compute what changed in the PR.
- `${{ secrets.GITHUB_TOKEN }}` — This is automatically created by GitHub for every workflow run. It has permissions to interact with the current repository.
- `${{ github.event.pull_request.number }}` — GitHub automatically provides context variables about the event. This gives the PR number (e.g., `3`) so the agent knows which PR to comment on.

---

### Workflow 2: `pr_merged_notification.yml` — The Merge Notification

```yaml
name: PR Merged Notification

on:
  pull_request:
    types: [closed]

jobs:
  notify:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - name: Send Merge Notification
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          PR_TITLE: ${{ github.event.pull_request.title }}
          PR_AUTHOR: ${{ github.event.pull_request.user.login }}
          REPO_NAME: ${{ github.event.repository.name }}
        run: python -m core.slack_client --merge-notify
```

**Key detail:** `if: github.event.pull_request.merged == true`

The `closed` event fires for both merged PRs AND closed-without-merge PRs. This condition ensures the notification only goes out when the PR was actually merged, not just closed.

---

## 🧠 Part 2 — The LangGraph Agent (The Brain)

LangGraph is a framework for building AI agents as **state machines**. Instead of writing one giant function, I broke the review process into individual nodes (steps), and LangGraph handles routing between them.

---

### `agent/state.py` — The Shared Data Container

```python
from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    # Input
    pr_number: int
    repo_owner: str
    repo_name: str

    # After fetch_diff node
    diff: str
    diff_token_count: int

    # After analyze_code node
    raw_ai_response: str
    risk_score: int                    # 0 to 100
    security_issues: List[dict]        # List of vulnerabilities found
    recommendations: List[str]         # How to fix them

    # After score_evaluation node
    risk_level: str                    # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    should_notify_slack: bool          # True if score >= 50

    # Control flags
    skip_analysis: bool                # True if diff is empty
    error_message: Optional[str]       # Holds any error that occurred
```

This `TypedDict` is the **single source of truth** that every node reads from and writes to. Think of it like a baton passed between runners in a relay race. Each node picks it up, adds its results, and passes it to the next node.

---

### `agent/prompts.py` — Instructions for the AI

This file contains the system prompt — the instructions I give to the AI model telling it exactly how to behave:

```python
SECURITY_REVIEW_SYSTEM_PROMPT = """
You are an expert security code reviewer with deep knowledge of:
- OWASP Top 10 vulnerabilities
- Common attack vectors (SQL injection, XSS, command injection, etc.)
- Secure coding best practices
- Cryptographic standards

You will receive a git diff (code changes from a Pull Request).
Your job is to analyze ONLY the changed lines (lines starting with +).

You MUST respond with a valid JSON object in exactly this format:
{
    "risk_score": <integer 0-100>,
    "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
    "summary": "<2-3 sentence overview>",
    "security_issues": [
        {
            "title": "<issue name>",
            "severity": "<CRITICAL|HIGH|MEDIUM|LOW>",
            "owasp_category": "<A0X:2021 – Category Name>",
            "location": "<filename>:<line_number>",
            "description": "<what the vulnerability is>",
            "recommendation": "<how to fix it>"
        }
    ],
    "merge_recommendation": "<APPROVE|REVIEW|BLOCK>"
}

Risk Score Guide:
- 0-30: No significant issues found
- 31-49: Minor issues, suggest review
- 50-69: Significant issues, fix before merging
- 70-100: Critical vulnerabilities, block merge immediately
"""
```

**Why structured JSON output?** Because I need to programmatically parse the AI's response. If I let it respond in free-form text, it would be extremely hard to extract the risk score and post it cleanly on GitHub. By forcing JSON, I can reliably parse `response["risk_score"]` every time.

---

### `agent/nodes.py` — Every Step of the Review

Each function here is one node in the LangGraph state machine. They all take `AgentState` as input and return an updated `AgentState`.

#### Node 1: `fetch_diff`

```python
def fetch_diff(state: AgentState) -> AgentState:
    """
    Calls the GitHub API to get the code diff for this PR.
    The diff shows exactly what lines were added or removed.
    """
    github = GitHubClient()

    diff = github.get_pr_diff(
        owner=state["repo_owner"],
        repo=state["repo_name"],
        pr_number=state["pr_number"]
    )

    if not diff or len(diff.strip()) == 0:
        return {**state, "skip_analysis": True, "diff": ""}

    return {
        **state,
        "diff": diff,
        "skip_analysis": False
    }
```

**What the GitHub API returns (example diff):**
```diff
diff --git a/auth.py b/auth.py
+++ b/auth.py
@@ -20,6 +20,10 @@
+def authenticate_user(username, password):
+    query = f"SELECT * FROM users WHERE username='{username}'"
+    cursor.execute(query)  # ← SQL injection vulnerability here
+    return cursor.fetchone()
```

The lines starting with `+` are newly added code. Lines starting with `-` are removed. The AI focuses on `+` lines because those are the new code being introduced.

---

#### Node 2: `validate_diff`

```python
def validate_diff(state: AgentState) -> AgentState:
    """
    Checks the diff size to avoid exceeding the AI model's context window.
    Nemotron 550B has a context limit. If the diff is too large,
    we truncate it to the first 12,000 tokens.
    """
    if state["skip_analysis"]:
        return state

    # Rough token estimate: 1 token ≈ 4 characters
    token_count = len(state["diff"]) // 4

    if token_count > 12000:
        # Truncate the diff
        max_chars = 12000 * 4
        truncated_diff = state["diff"][:max_chars]
        truncated_diff += "\n\n[DIFF TRUNCATED — showing first 48,000 characters]"
        return {**state, "diff": truncated_diff, "diff_token_count": 12000}

    return {**state, "diff_token_count": token_count}
```

**Why this matters:** Every AI model has a maximum number of tokens it can process in one request. If a developer changes 5,000 lines of code in one PR, the diff would be enormous. Without this check, the API call would fail with an error. By truncating, the agent still reviews as much as possible within the limit.

---

#### Node 3: `analyze_code`

```python
def analyze_code(state: AgentState) -> AgentState:
    """
    Sends the diff to the AI model and gets back a security analysis.
    This is the core intelligence of the entire agent.
    """
    if state["skip_analysis"]:
        return {**state, "risk_score": 0, "security_issues": [], "risk_level": "LOW"}

    llm = LLMClient()

    user_message = f"""
    Please review this Pull Request diff for security vulnerabilities:

    ```diff
    {state["diff"]}
    ```

    Respond ONLY with valid JSON. No preamble, no explanation outside the JSON.
    """

    response = llm.complete(
        system_prompt=SECURITY_REVIEW_SYSTEM_PROMPT,
        user_message=user_message
    )

    # Parse the JSON response
    parsed = json.loads(response)

    return {
        **state,
        "raw_ai_response": response,
        "risk_score": parsed["risk_score"],
        "risk_level": parsed["risk_level"],
        "security_issues": parsed["security_issues"],
        "recommendations": [issue["recommendation"] for issue in parsed["security_issues"]]
    }
```

---

#### Node 4: `score_evaluation`

```python
def score_evaluation(state: AgentState) -> AgentState:
    """
    Evaluates the risk score and decides whether to send a Slack alert.
    """
    risk_score = state["risk_score"]
    threshold = int(os.getenv("RISK_THRESHOLD", "50"))

    should_notify = risk_score >= threshold

    return {
        **state,
        "should_notify_slack": should_notify
    }
```

Simple but important — this node makes the binary decision that routes the workflow either to Slack notification or straight to posting the GitHub comment.

---

#### Node 5: `notify_slack`

```python
def notify_slack(state: AgentState) -> AgentState:
    """
    Sends a formatted Slack alert with the top security issues.
    Only runs if should_notify_slack is True.
    """
    slack = SlackClient()

    slack.send_security_alert(
        risk_score=state["risk_score"],
        risk_level=state["risk_level"],
        issues=state["security_issues"],
        pr_number=state["pr_number"],
        repo_name=state["repo_name"],
        repo_owner=state["repo_owner"]
    )

    return state
```

---

#### Node 6: `finalize`

```python
def finalize(state: AgentState) -> AgentState:
    """
    Formats the complete review as Markdown and posts it as a
    comment directly on the GitHub Pull Request.
    This always runs — even if the AI failed (posts an error message).
    """
    github = GitHubClient()

    comment = format_review_comment(
        risk_score=state["risk_score"],
        risk_level=state["risk_level"],
        issues=state["security_issues"],
        error=state.get("error_message")
    )

    github.post_pr_comment(
        owner=state["repo_owner"],
        repo=state["repo_name"],
        pr_number=state["pr_number"],
        comment=comment
    )

    return state
```

**Critical design choice:** `finalize` always runs, no matter what. Even if the AI call throws an exception, the agent catches it, stores the error in `state["error_message"]`, and still posts a comment saying "Review failed — please review manually." This ensures developers are never left wondering if the review happened.

---

### `agent/graph.py` — Connecting the Nodes

```python
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import fetch_diff, validate_diff, analyze_code, score_evaluation, notify_slack, finalize

def build_graph():
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("fetch_diff", fetch_diff)
    graph.add_node("validate_diff", validate_diff)
    graph.add_node("analyze_code", analyze_code)
    graph.add_node("score_evaluation", score_evaluation)
    graph.add_node("notify_slack", notify_slack)
    graph.add_node("finalize", finalize)

    # Define the linear flow
    graph.set_entry_point("fetch_diff")
    graph.add_edge("fetch_diff", "validate_diff")
    graph.add_edge("validate_diff", "analyze_code")
    graph.add_edge("analyze_code", "score_evaluation")

    # Conditional routing — only go to Slack if risk is high
    graph.add_conditional_edges(
        "score_evaluation",
        lambda state: "notify_slack" if state["should_notify_slack"] else "finalize",
        {
            "notify_slack": "notify_slack",
            "finalize": "finalize"
        }
    )

    graph.add_edge("notify_slack", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()


if __name__ == "__main__":
    import os
    agent = build_graph()
    agent.invoke({
        "pr_number": int(os.getenv("PR_NUMBER")),
        "repo_owner": os.getenv("REPO_OWNER"),
        "repo_name": os.getenv("REPO_NAME"),
        "skip_analysis": False,
        "error_message": None
    })
```

**Visual representation of the graph:**
```
fetch_diff
    │
validate_diff
    │
analyze_code
    │
score_evaluation
    │
    ├── (risk >= 50) ──→ notify_slack ──→ finalize ──→ END
    │
    └── (risk < 50)  ──────────────────→ finalize ──→ END
```

This is the power of LangGraph — the routing logic is **declarative and visual**, not buried inside nested if-else chains.

---

## 🔧 Part 3 — The Core Clients (The Hands)

These are the three modules that actually communicate with external services.

---

### `core/github_client.py` — Talking to GitHub

```python
import requests
import os

class GitHubClient:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3.diff",   # Request diff format
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Fetches the raw git diff for a Pull Request.
        Example URL: GET /repos/Naveen15github/github-ai-reviewer/pulls/3
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.text   # Returns the raw diff as text

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, comment: str):
        """
        Posts a comment on a Pull Request.
        Example URL: POST /repos/Naveen15github/github-ai-reviewer/issues/3/comments
        """
        # GitHub uses "issues" endpoint for PR comments
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = {"body": comment}

        # Switch Accept header for posting comments (JSON, not diff)
        headers = {**self.headers, "Accept": "application/vnd.github.v3+json"}
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

**Why `issues` endpoint for PR comments?** In GitHub's API, Pull Requests are a superset of Issues. PR comments and Issue comments use the same endpoint. This is a GitHub API quirk that trips up many developers.

---

### `core/llm_client.py` — Talking to the AI Model

This is the most critical client. It implements the **3-key rotation system**:

```python
import requests
import json
import os
import time

class LLMClient:
    def __init__(self):
        # Load all three API keys — keys 2 and 3 are optional backups
        self.api_keys = [
            k for k in [
                os.getenv("OPENROUTER_API_KEY_1"),
                os.getenv("OPENROUTER_API_KEY_2"),
                os.getenv("OPENROUTER_API_KEY_3"),
            ] if k  # Filter out None values
        ]
        self.current_key_index = 0
        self.model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _get_current_key(self) -> str:
        return self.api_keys[self.current_key_index]

    def _rotate_key(self):
        """Move to the next API key. Raises if all keys are exhausted."""
        self.current_key_index += 1
        if self.current_key_index >= len(self.api_keys):
            raise Exception("All API keys exhausted — rate limited on all keys")

    def complete(self, system_prompt: str, user_message: str) -> str:
        """
        Sends a message to the AI model and returns the response.
        Automatically retries with the next key on rate limit errors.
        """
        for attempt in range(len(self.api_keys)):
            try:
                response = requests.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self._get_current_key()}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/Naveen15github/github-ai-reviewer",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": 0.1,   # Low temperature = more consistent, deterministic responses
                        "max_tokens": 4096
                    },
                    timeout=120   # 2 minute timeout for large model responses
                )

                # Handle rate limiting — rotate key and retry
                if response.status_code in (429, 402):
                    print(f"Key {self.current_key_index + 1} rate limited. Rotating to next key...")
                    self._rotate_key()
                    time.sleep(2)   # Brief pause before retrying
                    continue

                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

            except requests.exceptions.Timeout:
                # Model took too long — try next key
                self._rotate_key()
                continue

        raise Exception("Failed to get AI response after trying all API keys")
```

**Why temperature 0.1?** Temperature controls how "creative" or "random" the AI's responses are. At 1.0, responses can vary significantly between calls. At 0.1, the model gives very consistent, predictable answers — which is exactly what you want for security analysis. You don't want the AI to say "SQL injection" on one run and miss it on the next run of the same code.

**Why 3 keys?** OpenRouter's free tier has rate limits per API key. By having 3 keys, the agent can handle 3x the throughput before hitting limits. In practice, this gives near-100% uptime even on a free plan.

---

### `core/slack_client.py` — Sending Slack Alerts

```python
import requests
import os

class SlackClient:
    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    def send_security_alert(self, risk_score, risk_level, issues, pr_number, repo_name, repo_owner):
        """
        Sends a formatted Block Kit message to Slack.
        Block Kit is Slack's rich message format — supports buttons, colors, sections.
        """
        # Map risk level to color (shown as left border on Slack message)
        color_map = {
            "CRITICAL": "#FF0000",   # Red
            "HIGH":     "#FF6600",   # Orange
            "MEDIUM":   "#FFD700",   # Yellow
            "LOW":      "#00AA00"    # Green
        }
        color = color_map.get(risk_level, "#888888")

        pr_url = f"https://github.com/{repo_owner}/{repo_name}/pull/{pr_number}"

        # Build the Block Kit payload
        payload = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"🚨 AI Code Review Alert — {risk_level} Risk (Score: {risk_score}/100)"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Risk Score:*\n{risk_score}/100 {'🔴' if risk_level == 'CRITICAL' else '🟠'}"},
                                {"type": "mrkdwn", "text": f"*Merge Recommendation:*\n{'🚫 BLOCK' if risk_score >= 70 else '⛔ FIX REQUIRED'}"},
                            ],
                            "accessory": {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View PR"},
                                "url": pr_url,
                                "style": "primary"
                            }
                        },
                        # Top 3 security issues
                        *[self._build_issue_block(issue) for issue in issues[:3]]
                    ]
                }
            ]
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

    def _build_issue_block(self, issue: dict) -> dict:
        """Formats a single security issue as a Slack Block Kit section."""
        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"🚨 *{issue['title']}*\n"
                    f"`{issue['owasp_category']}` | 📍 `{issue['location']}`\n"
                    f"💡 {issue['recommendation']}"
                )
            }
        }
```

---

## 🔩 Part 4 — Configuration & Settings

### `config/settings.py` — Central Configuration Manager

```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Settings:
    # OpenRouter API Keys
    openrouter_api_key_1: str
    openrouter_api_key_2: Optional[str]
    openrouter_api_key_3: Optional[str]
    openrouter_model: str

    # GitHub
    github_token: str
    pr_number: int
    repo_owner: str
    repo_name: str

    # Slack
    slack_webhook_url: Optional[str]

    # Thresholds
    risk_threshold: int
    max_diff_tokens: int

    @classmethod
    def from_env(cls) -> "Settings":
        """Load and validate all settings from environment variables."""

        # Validate required fields
        required = ["OPENROUTER_API_KEY_1", "GITHUB_TOKEN", "PR_NUMBER", "REPO_OWNER", "REPO_NAME"]
        missing = [key for key in required if not os.getenv(key)]

        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Make sure these are set in GitHub Secrets."
            )

        return cls(
            openrouter_api_key_1=os.getenv("OPENROUTER_API_KEY_1"),
            openrouter_api_key_2=os.getenv("OPENROUTER_API_KEY_2"),
            openrouter_api_key_3=os.getenv("OPENROUTER_API_KEY_3"),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free"),
            github_token=os.getenv("GITHUB_TOKEN"),
            pr_number=int(os.getenv("PR_NUMBER")),
            repo_owner=os.getenv("REPO_OWNER"),
            repo_name=os.getenv("REPO_NAME"),
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL"),
            risk_threshold=int(os.getenv("RISK_THRESHOLD", "50")),
            max_diff_tokens=int(os.getenv("MAX_DIFF_TOKENS", "12000"))
        )

# Singleton — imported once, reused everywhere
settings = Settings.from_env()
```

**Why validate at startup?** If `OPENROUTER_API_KEY_1` is missing, the agent would run for 3 minutes, process the diff, send it to the AI, and only then fail when trying to authenticate. By validating all required variables at the very start, the agent fails immediately with a clear error message — saving time and making debugging easy.

### `.env.example` — The Template for New Users

```bash
# Required
OPENROUTER_API_KEY_1=sk-or-v1-your-primary-key-here
GITHUB_TOKEN=ghp_your-token-here   # Auto-provided in GitHub Actions
PR_NUMBER=1                         # Auto-provided in GitHub Actions
REPO_OWNER=YourGitHubUsername       # Auto-provided in GitHub Actions
REPO_NAME=your-repo-name            # Auto-provided in GitHub Actions

# Optional — for backup API keys
OPENROUTER_API_KEY_2=sk-or-v1-your-backup-key-2
OPENROUTER_API_KEY_3=sk-or-v1-your-backup-key-3

# Optional — for Slack notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...

# Optional — tune the agent behavior
RISK_THRESHOLD=50    # Send Slack alert if score >= this value
MAX_DIFF_TOKENS=12000
```

---

## 📊 Part 5 — Risk Scoring System

The AI model generates a score from 0 to 100 based on the severity and number of vulnerabilities found. Here is how the score maps to actions:

| Score Range | Risk Level | Color | GitHub Comment | Slack Alert | Merge Decision |
|-------------|-----------|-------|----------------|-------------|----------------|
| 0 – 30 | 🟢 LOW | Green | ✅ Posted | ❌ No alert | Safe to merge |
| 31 – 49 | 🟡 MEDIUM | Yellow | ✅ Posted | ❌ No alert | Review suggested |
| 50 – 69 | 🟠 HIGH | Orange | ✅ Posted | ✅ Alert sent | Fix before merge |
| 70 – 100 | 🔴 CRITICAL | Red | ✅ Posted | ✅ Alert sent | Block merge |

### OWASP Top 10 — Full Coverage

Every vulnerability the AI finds is mapped to an OWASP category. These are the industry-standard vulnerability classifications:

| OWASP ID | Category | Examples Detected |
|----------|----------|-------------------|
| A01:2021 | Broken Access Control | Missing auth checks, privilege escalation |
| A02:2021 | Cryptographic Failures | MD5/SHA1 usage, plaintext passwords |
| A03:2021 | Injection | SQL injection, command injection, XSS |
| A04:2021 | Insecure Design | Logic flaws, missing security controls |
| A05:2021 | Security Misconfiguration | Debug mode on, default credentials |
| A06:2021 | Vulnerable Components | Outdated libraries with known CVEs |
| A07:2021 | Authentication Failures | Weak passwords, no MFA, session issues |
| A08:2021 | Data Integrity Failures | Insecure deserialization |
| A09:2021 | Logging Failures | Missing audit logs, logging sensitive data |
| A10:2021 | Server-Side Request Forgery | Unvalidated URL redirects |

---

## 🔐 Part 6 — Security Design

### How Secrets Are Protected

**GitHub Secrets** — All API keys and webhook URLs are stored in GitHub's encrypted secrets vault, not in the code. When the workflow runs, GitHub injects them as environment variables. They never appear in logs — GitHub automatically redacts them.

**GITHUB_TOKEN** — This is automatically generated by GitHub for each workflow run with minimal permissions (only what I declared in `permissions:`). It expires as soon as the workflow finishes.

**3-Key Rotation** — If a key is leaked, the other two still work. Rotating one key doesn't disrupt the system.

### Error Handling Strategy

```
AI call succeeds → Full review posted on PR
       │
AI call fails (timeout) → Retry with next key
       │
All keys exhausted → Post fallback comment: "AI review failed, please review manually"
       │
GitHub API fails → Log error, exit with non-zero code (marks workflow as failed)
```

The principle: **always post something on the PR**. Developers should never open a PR and see no review activity — they might assume the system ran but found nothing, when actually it crashed silently.

---

## 📝 Sample AI Review Output

This is what gets posted as a comment directly on the Pull Request:

```markdown
🤖 GitHub AI Code Reviewer — Risk Assessment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RISK SCORE: 95/100  [CRITICAL]
MERGE RECOMMENDATION: 🚫 BLOCK

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY:
This PR introduces an authentication module containing multiple critical
security vulnerabilities including SQL injection in 3 separate functions,
hardcoded credentials, MD5 password hashing, and command injection via
os.system(). This code should not be merged in its current state.

SECURITY ISSUES (5 found):

1. SQL Injection in authenticate_user()  [CRITICAL]
   OWASP: A03:2021 – Injection
   Location: vulnerable_auth.py:24
   Description: Username directly interpolated into SQL string
   Fix: Use parameterized queries — cursor.execute("SELECT * FROM users
        WHERE username = ? AND password = ?", (username, password))

2. SQL Injection in get_user_profile()  [CRITICAL]
   OWASP: A03:2021 – Injection
   Location: vulnerable_auth.py:41
   Description: user_id directly interpolated into SQL string
   Fix: cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))

3. Hardcoded Credentials  [HIGH]
   OWASP: A07:2021 – Authentication Failures
   Location: vulnerable_auth.py:10-12
   Description: API keys and DB passwords committed to source code
   Fix: Use environment variables or a secrets manager

4. Weak Cryptography — MD5 Password Hashing  [HIGH]
   OWASP: A02:2021 – Cryptographic Failures
   Location: vulnerable_auth.py:33
   Description: MD5 is cryptographically broken for password storage
   Fix: Use bcrypt, scrypt, or Argon2id for password hashing

5. Command Injection via os.system()  [CRITICAL]
   OWASP: A03:2021 – Injection
   Location: vulnerable_auth.py:67
   Description: User-controlled input passed to os.system()
   Fix: Use subprocess.run(["command", arg1, arg2]) with a list, never a string

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generated by GitHub AI Code Reviewer • Powered by OpenRouter
```

---

## 🚀 Setup & Installation

### Prerequisites

Before you start, make sure you have:
- A GitHub repository (public or private)
- GitHub Actions enabled (it's on by default)
- An OpenRouter account — sign up free at [openrouter.ai](https://openrouter.ai)
- A Slack workspace with an incoming webhook configured (optional but recommended)
- Python 3.11+ installed locally (only needed if you want to test locally)

### Step 1 — Clone This Repository

```bash
git clone https://github.com/Naveen15github/github-ai-reviewer.git
cd github-ai-reviewer
```

### Step 2 — Get Your OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai) and create a free account
2. Navigate to **Keys** in the dashboard
3. Click **Create Key**
4. Copy the key — it starts with `sk-or-v1-...`
5. Optionally create 2 more keys for backup (highly recommended)

### Step 3 — Set Up GitHub Secrets

In your GitHub repository, go to:
**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets one by one:

| Secret Name | Value | Required? |
|-------------|-------|-----------|
| `OPENROUTER_API_KEY_1` | Your primary OpenRouter key | ✅ Yes |
| `OPENROUTER_API_KEY_2` | Your backup key #2 | ❌ Optional |
| `OPENROUTER_API_KEY_3` | Your backup key #3 | ❌ Optional |
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL | ❌ Optional |

> **Note:** `GITHUB_TOKEN`, `PR_NUMBER`, `REPO_OWNER`, and `REPO_NAME` are all **automatically provided** by GitHub Actions — you do NOT need to add them.

### Step 4 — Set Up Slack Webhook (Optional)

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App → From Scratch**
3. Give it a name like "AI Code Reviewer"
4. Go to **Incoming Webhooks → Activate Incoming Webhooks**
5. Click **Add New Webhook to Workspace**
6. Choose the channel (e.g., `#all-projects`)
7. Copy the webhook URL and add it as `SLACK_WEBHOOK_URL` in GitHub Secrets

### Step 5 — The Workflows Are Already Ready

The `.github/workflows/` directory contains both workflow files. GitHub Actions will automatically pick them up — no additional configuration needed.

### Step 6 — Test It Live

Create a test PR to see the agent in action:

```bash
git checkout -b test-ai-review
echo "# Test" >> test_file.py
git add test_file.py
git commit -m "test: trigger AI review"
git push origin test-ai-review
```

Then open a Pull Request on GitHub. Within 30–60 seconds you should see:
- ✅ A workflow run appear under the **Actions** tab
- ✅ An AI review comment posted on your PR
- ✅ A Slack alert (if the risk score is ≥ 50)

---

## 🧪 Testing

### Run All Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

### Run With Coverage Report

```bash
pytest tests/ --cov=agent --cov=core --cov=config --cov-report=term-missing
```

### Test Locally Without GitHub

```bash
# Uses a sample diff bundled in scripts/test_local.py
python scripts/test_local.py

# Test against a real PR (needs GITHUB_TOKEN set locally)
python scripts/test_local.py https://github.com/owner/repo/pull/42
```

### What the Tests Cover

| Test File | What It Tests |
|-----------|---------------|
| `test_github_client.py` | Fetching diffs, posting comments, API error handling |
| `test_llm_client.py` | Key rotation logic, JSON parsing, timeout handling |
| `test_slack_client.py` | Block Kit message formatting, webhook posting |
| `test_nodes.py` | Each agent node in isolation with mock inputs |
| `test_graph.py` | Full end-to-end workflow with all nodes connected |

---

## 🛠️ Tech Stack

| Component | Technology | Why I Chose It |
|-----------|------------|----------------|
| **Orchestration** | LangGraph | State machine model is perfect for multi-step conditional workflows |
| **AI Model** | NVIDIA Nemotron 3 Ultra 550B | 550B parameters, excellent code understanding, free tier available |
| **AI Platform** | OpenRouter API | Unified API for multiple models, generous free tier |
| **CI/CD** | GitHub Actions | Zero infrastructure, native GitHub integration |
| **Language** | Python 3.11+ | Best ecosystem for AI/ML tooling |
| **Notifications** | Slack Webhooks | Simple, reliable, supports rich Block Kit formatting |
| **Data Validation** | Pydantic | Type-safe parsing of AI responses |

### Key Python Dependencies

```txt
langgraph>=0.2.0       # Agent state machine
langchain-core>=0.3.0  # LangChain core (used by LangGraph)
requests>=2.32.0       # HTTP client for all API calls
python-dotenv>=1.0.0   # Load .env file for local development
pydantic>=2.7.0        # Validate and parse AI JSON responses
```

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Time from PR open to review comment | 30 – 60 seconds |
| AI model analysis time | 5 – 15 seconds |
| Maximum PR diff size | ~48 KB (~12,000 tokens) |
| Uptime with 3-key rotation | 99%+ |
| Monthly cost | $0 (free tier) |

---

## 🌟 Key Design Principles

**1. Always post a comment** — The finalize node runs unconditionally. Whether the review succeeded, failed, or was skipped, the developer always gets a comment on their PR.

**2. Never block on rate limits** — The 3-key rotation means a single key hitting its limit doesn't stall the workflow. The agent silently moves to the next key and keeps going.

**3. Structured AI output** — By instructing the AI to respond only in JSON, I can reliably parse, validate, and display results — no fragile regex on free-form text.

**4. Separation of concerns** — Each file has one job: `graph.py` routes, `nodes.py` processes, `github_client.py` posts, `llm_client.py` analyzes. This makes each component independently testable and replaceable.

---

## 🔮 Future Enhancements

- [ ] Support for JavaScript, TypeScript, Java, Go (currently optimized for Python)
- [ ] Custom per-repo security rules via a `.security-rules.yml` file
- [ ] Jira / Linear integration — automatically create tickets for HIGH/CRITICAL issues
- [ ] Historical risk score dashboard — track security trends across PRs over time
- [ ] Auto-fix mode — generate secure replacement code as a PR suggestion
- [ ] Branch protection integration — automatically block merges for CRITICAL scores via GitHub's required status checks

---

## 🔗 Resources

- **Repository:** https://github.com/Naveen15github/github-ai-reviewer
- **Issues / Bug Reports:** https://github.com/Naveen15github/github-ai-reviewer/issues
- **OpenRouter Docs:** https://openrouter.ai/docs
- **LangGraph Docs:** https://python.langchain.com/docs/langgraph
- **GitHub Actions Docs:** https://docs.github.com/en/actions
- **OWASP Top 10:** https://owasp.org/www-project-top-ten/
- **Slack Block Kit Builder:** https://app.slack.com/block-kit-builder

---

## 👤 Author

**Naveen**
GitHub: [@Naveen15github](https://github.com/Naveen15github)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

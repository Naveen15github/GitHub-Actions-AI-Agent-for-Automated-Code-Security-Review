# 🤖 GitHub AI Code Reviewer

An automated Pull Request review agent that triggers on every GitHub PR, analyses
the code diff using a large language model via OpenRouter, scores security and
quality risks against OWASP Top 10, and sends Slack alerts when the risk score
exceeds a configurable threshold.

**Features:**
- 🔍 **Automated Code Review** — AI analyzes every PR for security and quality issues
- 🚨 **Slack Alerts** — Notifications for high-risk PRs (score ≥ 50)
- ✅ **Merge Notifications** — Get notified when any PR is merged
- 🔄 **3-Key Rotation** — Automatic failover for rate limit handling
- 📊 **OWASP Scoring** — Risk assessment based on OWASP Top 10
- 💬 **GitHub Comments** — Review posted directly on PRs

---

## 📐 Architecture

```
GitHub Pull Request
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                  │
│                   (.github/workflows/ai_review.yml)      │
└──────────────────────────┬──────────────────────────────┘
                           │  python -m agent.graph
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    LangGraph Agent                        │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐                    │
│  │ fetch_diff  │───▶│validate_diff │                    │
│  │    node     │    │    node      │                    │
│  └─────────────┘    └──────┬───────┘                    │
│                            │ valid?                      │
│                    ┌───────┴───────┐                     │
│                   YES             NO                     │
│                    │               │                     │
│                    ▼               ▼                     │
│           ┌──────────────┐  ┌──────────────┐            │
│           │ analyze_code │  │   finalize   │            │
│           │    node      │  │    node      │            │
│           └──────┬───────┘  └──────────────┘            │
│                  ▼                                       │
│         ┌───────────────┐                               │
│         │score_evaluation│                               │
│         │    node       │                               │
│         └───────┬───────┘                               │
│                 │ score >= 50?                           │
│         ┌───────┴────────┐                              │
│        YES              NO                              │
│         │                │                              │
│         ▼                ▼                              │
│  ┌─────────────┐  ┌──────────────┐                     │
│  │notify_slack │  │   finalize   │                     │
│  │    node     │  │    node      │                     │
│  └──────┬──────┘  └──────────────┘                     │
│         │                                               │
│         ▼                                               │
│  ┌──────────────┐                                       │
│  │   finalize   │                                       │
│  │    node      │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
        │                              │
        ▼                              ▼
  GitHub PR Comment              Slack Alert
  (posted on every PR)      (high-risk PRs only)
```

**Key integrations:**
- **OpenRouter** — Provides LLM access with 3-key rotation fallback
- **GitHub API** — Fetches PR diff, posts review comment
- **Slack Webhooks** — Sends Block Kit rich alerts for risky PRs
- **LangGraph** — Orchestrates the multi-node review pipeline

---

## ✅ Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Earlier versions may work but are untested |
| Git | Any | For cloning the repo |
| GitHub account | — | To create repos and PRs |
| OpenRouter account | — | Free tier available — see below |
| Slack workspace | — | Optional, needed for alerts |

---

## 🚀 Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-org/github-ai-reviewer.git
cd github-ai-reviewer
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Now edit .env with your real values (see sections below)
```

---

## 🔑 Getting OpenRouter API Keys

OpenRouter gives you access to hundreds of AI models through a single API, including
free models like the one this project uses by default.

1. Go to [https://openrouter.ai](https://openrouter.ai) and click **Sign Up**
2. Verify your email address
3. In the dashboard, click your profile → **API Keys**
4. Click **Create Key** — give it a name like `github-reviewer-1`
5. Copy the key (starts with `sk-or-v1-`) and paste it into your `.env` as `OPENROUTER_API_KEY_1`
6. Repeat for keys 2 and 3 (optional but recommended for rotation)

> **Free tier:** The default model `nvidia/llama-3.1-nemotron-ultra-253b-v1:free` is
> completely free. No credit card required for free models.

---

## 💬 Setting Up Slack Webhooks

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **Create New App** → **From scratch**
3. Name it (e.g. `AI Code Reviewer`) and pick your workspace
4. Under **Features**, click **Incoming Webhooks**
5. Toggle **Activate Incoming Webhooks** to ON
6. Click **Add New Webhook to Workspace**
7. Select the channel where alerts should appear (e.g. `#code-reviews`)
8. Click **Allow**
9. Copy the **Webhook URL** (starts with `https://hooks.slack.com/services/...`)
10. Paste it into your `.env` as `SLACK_WEBHOOK_URL`

> **Tip:** Create a dedicated `#ai-code-review-alerts` channel so high-risk
> PR alerts don't clutter your main channels.

---

## 🔐 Adding GitHub Secrets

GitHub Actions reads secrets from your repo's settings rather than committed files.

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each of the following:

| Secret Name | Value |
|-------------|-------|
| `OPENROUTER_API_KEY_1` | Your first OpenRouter API key |
| `OPENROUTER_API_KEY_2` | Your second OpenRouter API key (optional) |
| `OPENROUTER_API_KEY_3` | Your third OpenRouter API key (optional) |
| `SLACK_WEBHOOK_URL` | Your Slack webhook URL (optional) |

> **Note:** `GITHUB_TOKEN` is provided automatically by GitHub Actions — you
> do **not** need to add it as a secret.

---

## ⚡ Triggering the Agent

The agent runs automatically on every pull request event.

### Trigger it:
1. Push a branch to your repository
2. Open a Pull Request on GitHub (or synchronise an existing one)
3. Navigate to **Actions** tab — you'll see the `AI Code Review` workflow running

### What to expect:
- The workflow completes in ~30–90 seconds depending on diff size and LLM latency
- A comment is posted directly on your PR with the full review
- If the risk score is ≥ 50, a Slack notification is sent to your configured channel
- The GitHub Actions job exits with code `0` (success) or `1` (critical errors)

---

## 🧪 Running Tests Locally

```bash
# Run the full test suite
pytest tests/ -v

# Run a specific test file
pytest tests/test_llm_client.py -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=agent --cov=core --cov=config --cov-report=term-missing

# Run only fast unit tests (skip integration)
pytest tests/ -v -k "not graph"
```

### Expected output (abbreviated):

```
tests/test_llm_client.py::TestOpenRouterClientSuccess::test_complete_returns_content_on_success PASSED
tests/test_llm_client.py::TestKeyRotationOn429::test_rotates_to_second_key_on_429 PASSED
tests/test_llm_client.py::TestAllKeysFailing::test_raises_runtime_error_when_all_keys_429 PASSED
tests/test_github_client.py::TestGetPrDiff::test_returns_diff_text_on_success PASSED
tests/test_github_client.py::TestPostPrComment::test_returns_true_on_success PASSED
tests/test_slack_client.py::TestSlackMessageStructure::test_critical_review_uses_red_color PASSED
tests/test_nodes.py::TestFetchDiffNode::test_returns_diff_on_success PASSED
tests/test_graph.py::TestGraphHighRiskPath::test_slack_sent_true_for_high_risk PASSED
...
32 passed in 1.84s
```

---

## 🛠️ Local End-to-End Test (scripts/test_local.py)

The `test_local.py` script lets you run the full pipeline locally without opening
a real PR. It uses a built-in sample diff with intentional vulnerabilities.

### Run with built-in sample diff (no GitHub token needed for diff fetch):

```bash
python scripts/test_local.py
```

### Run against a real PR:

```bash
python scripts/test_local.py https://github.com/your-org/your-repo/pull/42
```

### Options:

```bash
# Suppress Slack notification
python scripts/test_local.py --no-slack

# Skip posting GitHub PR comment
python scripts/test_local.py --no-comment

# Combine flags
python scripts/test_local.py https://github.com/org/repo/pull/5 --no-slack --no-comment
```

### Sample output:

```
✅  Loaded environment variables from .env
ℹ️   No PR URL provided — using built-in sample diff
🚀  Running LangGraph agent pipeline...

======================================================================
 🤖  GitHub AI Code Reviewer — Local Test Run
======================================================================

  Pipeline Status : SUCCESS
  OpenRouter Key  : Key #1 (used for LLM call)
  Slack Sent      : ✅ Yes
  GitHub Comment  : ✅ Posted

  RISK SCORE: 85/100  [CRITICAL]

  SUMMARY
    Multiple critical security vulnerabilities detected including SQL
    injection and hardcoded secrets. This PR must not be merged.

  MERGE RECOMMENDATION: 🚫 BLOCK

  SECURITY ISSUES (3 found)
    1. SQL Injection — [CRITICAL]
       OWASP    : A03:2021 – Injection
       Location : app/auth.py:12
       ...
```

---

## 🔧 Troubleshooting

### "Missing required environment variables" error

Make sure your `.env` file exists and is properly filled in:
```bash
cat .env | grep -v "^#" | grep -v "^$"
```

### "All 3 OpenRouter API key(s) failed"

- Check your keys are correctly copied (no trailing spaces, include `sk-or-v1-` prefix)
- Verify the model name is correct: go to https://openrouter.ai/models and search
- Free model quotas reset daily — try again in a few hours

### GitHub Actions workflow not triggering

- Ensure the `.github/workflows/ai_review.yml` file is on your default branch (`main`)
- Check the PR is targeting your default branch
- Verify the workflow file has no YAML syntax errors: paste it into https://yaml-online-parser.appspot.com

### "403 Forbidden" when posting PR comment

- The `GITHUB_TOKEN` needs `pull_requests: write` permission
- In Actions workflow, ensure `permissions: pull-requests: write` is set (already in the provided workflow)
- For organisation repos, check branch protection rules aren't blocking the bot

### Slack messages not appearing

- Test the webhook directly:
  ```bash
  curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test from AI reviewer"}' \
    YOUR_SLACK_WEBHOOK_URL
  ```
- Should return `ok`. If not, regenerate the webhook in Slack app settings.

### LLM returns non-JSON response

- The agent catches this and falls back gracefully (risk_score=0, manual review recommended)
- Try switching to a different model by setting `OPENROUTER_MODEL` in `.env`
- Check OpenRouter status at https://status.openrouter.ai

---

## 📁 Project Structure

```
github-ai-reviewer/
│
├── .github/
│   └── workflows/
│       └── ai_review.yml     # GitHub Actions: triggers on PR events
│
├── agent/
│   ├── __init__.py
│   ├── graph.py              # LangGraph StateGraph: node wiring & routing logic
│   ├── nodes.py              # All LangGraph node functions (the actual logic)
│   ├── state.py              # TypedDict state schema shared between nodes
│   └── prompts.py            # System + user prompts sent to the LLM
│
├── core/
│   ├── __init__.py
│   ├── llm_client.py         # OpenRouter HTTP client with 3-key rotation
│   ├── github_client.py      # GitHub API: fetch PR diff, post comments
│   └── slack_client.py       # Slack Block Kit webhook sender
│
├── config/
│   ├── __init__.py
│   └── settings.py           # All config loaded from env vars; singleton instance
│
├── tests/
│   ├── __init__.py
│   ├── test_llm_client.py    # Key rotation, response parsing
│   ├── test_github_client.py # Diff fetching, comment posting
│   ├── test_slack_client.py  # Block Kit structure, colour mapping
│   ├── test_nodes.py         # Each node function in isolation
│   └── test_graph.py         # Full pipeline integration tests
│
├── scripts/
│   └── test_local.py         # CLI: run agent locally with sample or real PR diff
│
├── requirements.txt           # Python dependencies
├── .env.example              # Template for environment variables (safe to commit)
└── README.md                 # This file
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| **LangGraph** for orchestration | Explicit state machine makes routing conditions auditable and testable |
| **requests** (not OpenAI SDK) | Direct HTTP gives fine-grained control over headers, retries, and key rotation |
| **TypedDict** state | Type-safe state prevents silent key-name bugs across nodes |
| **3-key rotation** | Eliminates single points of failure for free-tier rate limits |
| **JSON-only LLM output** | Strict structured output enables reliable parsing and score extraction |
| **Fallback review** on LLM failure | Agent always finishes and posts a comment, even when the LLM is unavailable |

---

## 📄 Licence

MIT — see [LICENSE](LICENSE) for details.

---

*Built with [LangGraph](https://github.com/langchain-ai/langgraph) · [OpenRouter](https://openrouter.ai) · [GitHub Actions](https://docs.github.com/en/actions)*
#   T r i g g e r   r e - r u n 
 
 
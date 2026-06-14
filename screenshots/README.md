# 📸 Project Screenshots

This folder contains screenshots demonstrating the GitHub Actions AI Agent functionality.

---

## 📋 Screenshot Checklist

### **Essential Screenshots (Must-Have)**

#### **1. High-Risk PR Review** 🔴
- **File:** `01-high-risk-pr-review.png`
- **What to capture:** 
  - Full PR page with AI review comment
  - Risk score (70-100, CRITICAL/HIGH)
  - Security issues found (SQL injection, hardcoded secrets, etc.)
  - Merge recommendation: 🚫 BLOCK
- **Expected:** Red/orange alert styling

#### **2. Low-Risk PR Review** 🟢
- **File:** `02-low-risk-pr-review.png`
- **What to capture:**
  - PR page with AI review comment
  - Risk score (0-30, LOW)
  - Clean code feedback
  - Merge recommendation: ✅ APPROVE
- **Expected:** Green/safe styling

#### **3. GitHub Actions Workflow Success** ⚙️
- **File:** `03-github-actions-workflow.png`
- **What to capture:**
  - Actions tab with successful runs (green checkmarks)
  - Workflow name: "AI Code Review"
  - Multiple runs showing consistency
- **Shows:** Automation reliability

#### **4. Slack High-Risk Alert** 🚨
- **File:** `04-slack-high-risk-alert.png`
- **What to capture:**
  - Slack notification with red/orange styling
  - Risk score and security issues
  - "View PR" button
  - Timestamp showing real-time notification
- **Shows:** Team alerting in action

#### **5. Slack Merge Notification** ✅
- **File:** `05-slack-merge-notification.png`
- **What to capture:**
  - Green "✅ Pull Request Merged" message
  - PR details (author, merged by)
  - "View PR" button
- **Shows:** Complete workflow

---

### **Bonus Screenshots (Nice to Have)**

#### **6. GitHub Actions Workflow Logs** 📊
- **File:** `06-workflow-logs.png`
- **What to capture:**
  - Detailed logs showing AI analysis steps
  - Risk scoring process
  - Comment posting confirmation

#### **7. Repository Structure** 📁
- **File:** `07-repository-structure.png`
- **What to capture:**
  - Project folder structure
  - Key directories (agent/, core/, .github/workflows/)
  - Shows professional organization

#### **8. GitHub Secrets Configuration** 🔐
- **File:** `08-github-secrets.png`
- **What to capture:**
  - List of configured secrets (names only)
  - OPENROUTER_API_KEY_1, OPENROUTER_API_KEY_2, etc.
  - Shows security best practices

#### **9. Vulnerable Code Sample** ⚠️
- **File:** `09-vulnerable-code.png`
- **What to capture:**
  - Code with security issues
  - SQL injection example
  - Hardcoded credentials
  - Shows what the AI detects

#### **10. LangGraph Agent Code** 🤖
- **File:** `10-langgraph-agent.png`
- **What to capture:**
  - agent/graph.py file
  - StateGraph definition
  - Node routing logic
  - Shows technical implementation

---

## 📐 Screenshot Guidelines

### **Quality:**
- Resolution: Minimum 1920x1080
- Format: PNG (better quality than JPG)
- Clean: Remove unnecessary browser tabs/bookmarks

### **Content:**
- Show full context (don't crop important parts)
- Include timestamps where relevant
- Use dark mode for professional look
- Capture multiple examples showing different scenarios

### **Organization:**
Number files sequentially (01, 02, 03...) for easy reference in documentation.

---

## 🎯 Usage in README

These screenshots will be referenced in the main README.md file like:

```markdown
## 🎬 Demo

### High-Risk PR Detection
![High-Risk PR Review](screenshots/01-high-risk-pr-review.png)

### Slack Alerts
![Slack Alert](screenshots/04-slack-high-risk-alert.png)
```

---

## 📝 Notes

- Keep file sizes reasonable (compress if > 1MB)
- Update this checklist as you add more screenshots
- Add descriptive captions when using in documentation
- Screenshots should tell the story of how the agent works

---

**Last Updated:** June 14, 2026

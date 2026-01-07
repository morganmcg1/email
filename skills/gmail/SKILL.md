---
name: gmail
description: Manage email inbox including triage, prioritization, summaries, and automation rules. Use when checking emails, organizing inbox, setting up filters, asking about messages, or anything email-related.
---

# Gmail Email Assistant

This skill enables intelligent email management through the Gmail MCP server.

## Prerequisites: Gmail MCP Server

This skill requires the Gmail MCP server to be installed and configured.

### Step 1: Check if MCP Tools Available

Try calling `list_labels` or `get_emails`. If they work, skip to "Using This Skill".

If you get "tool not found" or similar error, the MCP server needs to be installed.

### Step 2: Install MCP Server (if not available)

Tell the user:
> "The Gmail MCP tools aren't available yet. I'll help you set them up."

Then guide them through:

**2a. Clone and install:**
```bash
git clone https://github.com/morganmcg1/email.git
cd email
uv venv && source .venv/bin/activate
uv pip install -e .
```

**2b. Set up Gmail API credentials:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Gmail API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Select "Desktop application"
6. Download the JSON file
7. Save it as `~/.email-assistant/credentials.json`

**2c. Configure Claude Desktop:**
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "email-assistant": {
      "command": "email-assistant"
    }
  }
}
```

**2d. Restart Claude Desktop** - the MCP server loads on startup.

### Step 3: Authenticate

On first use, call `authenticate`. This opens a browser for Google OAuth.
After authenticating, the token is saved at `~/.email-assistant/token.json`.

## Important: Use Subagents for Email Processing

Email content is large. To keep the main conversation context clean, always spawn a subagent for operations that read multiple emails.

**Pattern:**
```
1. Use Task tool with subagent_type: "general-purpose"
2. Instruct subagent to use Gmail MCP tools
3. Have it return only summarized results
4. Present results to user
```

## Quick Commands

### Check Inbox
Spawn a subagent to fetch and summarize unread emails:
```
Task prompt: "Use Gmail MCP tools to fetch unread emails (max 20).
Return a summary list with: sender, subject, one-line preview.
Do NOT include full email bodies."
```

### Triage Inbox
See [TRIAGE.md](TRIAGE.md) for full workflow. High-level:
1. Check if prioritization criteria exist (`get_prioritization_criteria`)
2. If not, interview user to gather criteria
3. Spawn subagent to fetch and score emails
4. Present prioritized list (HIGH/MEDIUM/LOW)

### Create Automation Rule
See [AUTOMATION.md](AUTOMATION.md). High-level:
1. Ask user for rule in natural language
2. Parse into structured conditions/actions
3. Save via `create_rule`
4. Offer dry-run to preview

### Run Automation
Execute saved rules:
```
run_automation(dry_run=true)  # Preview first
run_automation()              # Execute
```

## Available MCP Tools

### Core Email
- `get_emails` - Fetch emails with filters (query, unread_only, max_results)
- `search_emails` - Gmail query syntax search
- `get_email` - Get single email by ID
- `get_thread` - Get full email thread
- `archive_email` - Archive email(s)
- `trash_email` - Move email(s) to trash
- `mark_read` - Mark as read
- `modify_labels` - Add/remove labels
- `batch_label` - Modify labels on multiple emails
- `list_labels` - List all Gmail labels

### Triage
- `setup_prioritization` - Save user's priority criteria
- `get_prioritization_criteria` - Get saved criteria
- `clear_prioritization` - Reset criteria
- `triage_inbox` - Score emails (requires criteria set)

### Automation
- `create_rule` - Create automation rule
- `list_rules` - List all rules
- `delete_rule` - Delete a rule
- `run_automation` - Execute rules (supports dry_run)

## Gmail Query Syntax

Use with `search_emails`:
- `from:email@example.com` - From specific sender
- `to:me` - Sent directly to me
- `subject:meeting` - Subject contains word
- `is:unread` - Unread emails
- `has:attachment` - Has attachments
- `newer_than:7d` - Last 7 days
- `older_than:1m` - Older than 1 month
- `label:important` - Has label

## Email Summarization

To summarize a specific email or batch of emails:

1. Spawn subagent with prompt:
```
Use Gmail MCP tools to get_email(email_id) [or get_emails for batch].
Read the full content and provide for each email:
- 2-3 sentence summary of the main content
- Key action items mentioned (if any)
- Deadline or time-sensitive mentions (if any)
- Whether sender is asking a question or requesting something

Do NOT include the full email body in your response.
```

## Needs Reply Detection

To identify which emails need the user's reply:

1. Spawn subagent with prompt:
```
Use Gmail MCP tools to fetch recent emails. For each email, determine if it needs a reply.

NEEDS REPLY if:
- Contains a direct question to the user
- Requests action, response, or confirmation
- Is part of ongoing conversation awaiting user input
- Sender is explicitly or implicitly waiting on user

DOES NOT NEED REPLY if:
- Informational only (newsletters, notifications, digests)
- User already replied (check thread)
- User is CC'd only, not direct recipient
- Automated/transactional (receipts, shipping confirmations, alerts)
- Marketing or promotional

Return a list with:
- Sender name and email
- Subject line
- [REPLY NEEDED] or [NO REPLY NEEDED] flag
- Brief reason for the determination
```

## Supporting Files

- [TRIAGE.md](TRIAGE.md) - Detailed triage workflow
- [AUTOMATION.md](AUTOMATION.md) - Rule creation and execution
- [PRIORITIZATION.md](PRIORITIZATION.md) - Criteria schema and examples

# Email Assistant

MCP server for Gmail email triage and automation with Claude Code.

## Features

- **Email Triage**: Score emails as HIGH/MEDIUM/LOW priority based on YOUR criteria
- **Inbox Automation**: Create rules in natural language or structured format
- **Gmail Integration**: Full access to read, search, archive, label, and manage emails
- **Claude Code Skill**: Intelligent orchestration via `~/.claude/skills/gmail/`

## Architecture

```
┌─────────────────────────────────────┐
│  Claude Code + Gmail Skill          │
│  (Orchestration & AI)               │
└──────────────┬──────────────────────┘
               │ uses
               ▼
┌─────────────────────────────────────┐
│  Gmail MCP Server (this package)    │
│  (Data layer - Gmail API wrapper)   │
└─────────────────────────────────────┘
```

## Setup

### 1. Install

```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials JSON
6. Save as `~/.email-assistant/credentials.json`

### 3. Add to Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "email-assistant": {
      "command": "email-assistant"
    }
  }
}
```

### 4. Authenticate

When first using the tools, call `authenticate` to complete the OAuth flow.

## MCP Tools

### Core Email Tools

| Tool | Description |
|------|-------------|
| `get_emails` | Fetch emails with filters |
| `search_emails` | Gmail query syntax search |
| `get_email` | Get single email by ID |
| `get_thread` | Get full email thread |
| `modify_labels` | Add/remove labels |
| `archive_email` | Archive email(s) |
| `trash_email` | Move email(s) to trash |
| `batch_label` | Modify labels on multiple emails |
| `mark_read` | Mark as read |
| `list_labels` | List all labels |

### Triage Tools

| Tool | Description |
|------|-------------|
| `setup_prioritization` | Define your priority criteria |
| `get_prioritization_criteria` | View current criteria |
| `clear_prioritization` | Reset criteria |
| `triage_inbox` | Score emails (HIGH/MEDIUM/LOW) |

### Automation Tools

| Tool | Description |
|------|-------------|
| `create_rule` | Create automation rule |
| `list_rules` | List all rules |
| `delete_rule` | Delete a rule |
| `run_automation` | Execute rules (supports dry_run) |

## Usage with Claude Code

The Gmail skill teaches Claude Code how to manage email intelligently.

### Install Skill (one-time)
```bash
# Copy skill files to your global Claude skills directory
cp -r skills/gmail ~/.claude/skills/
```

The skill (`~/.claude/skills/gmail/`) teaches Claude Code how to:

### Triage Inbox
```
User: "Triage my inbox"
```
- Checks for existing priority criteria
- If none, runs interview to gather your preferences
- Spawns subagent to fetch and score emails
- Returns prioritized list

### Create Automation Rule
```
User: "Archive newsletters older than 7 days"
```
- Parses natural language into structured rule
- Saves rule via MCP
- Offers dry-run preview

### Run Automation
```
User: "Run my email rules"
```
- Executes all enabled rules
- Reports actions taken per rule

## Gmail Query Syntax

Use with `search_emails`:

| Query | Description |
|-------|-------------|
| `from:email@example.com` | From specific sender |
| `to:me` | Sent directly to me |
| `subject:meeting` | Subject contains word |
| `is:unread` | Unread emails |
| `has:attachment` | Has attachments |
| `newer_than:7d` | Last 7 days |
| `older_than:1m` | Older than 1 month |
| `label:important` | Has label |

## Development

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT

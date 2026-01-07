# Email Assistant

## Overview

This is a Gmail MCP server with an accompanying Claude Code skill for intelligent email management.

**Architecture:**
- `src/email_assistant/` - MCP server providing Gmail tools (data layer)
- `~/.claude/skills/gmail/` - Claude Code skill for orchestration (AI layer, installed globally)

## Components

### MCP Server

The server provides raw Gmail operations via MCP tools:

**Core Email Tools:**
- `get_emails`, `search_emails`, `get_email`, `get_thread`
- `archive_email`, `trash_email`, `mark_read`
- `modify_labels`, `batch_label`, `list_labels`

**Triage Tools:**
- `setup_prioritization` - Save user's priority criteria
- `get_prioritization_criteria` - Get saved criteria
- `triage_inbox` - Score emails (HIGH/MEDIUM/LOW)

**Automation Tools:**
- `create_rule`, `list_rules`, `delete_rule`
- `run_automation` - Execute rules (supports dry_run)

### Gmail Skill

Installed globally at `~/.claude/skills/gmail/`, this skill instructs Claude Code how to:
- Triage inbox using user-defined criteria
- Create automation rules from natural language
- Spawn subagents for email processing (context management)

See `~/.claude/skills/gmail/SKILL.md` for full documentation.

## Setup

### 1. Install Dependencies
```bash
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 2. Gmail API Credentials
1. Go to Google Cloud Console
2. Enable Gmail API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `~/.email-assistant/credentials.json`

### 3. Configure Claude Desktop
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

### 4. Authenticate
Run any email tool - it will trigger OAuth flow on first use.

## Usage Patterns

### Triage Inbox
User: "Triage my inbox"
- If no criteria: Skill runs interview to gather preferences
- Spawns subagent to fetch and score emails
- Returns prioritized list (HIGH/MEDIUM/LOW)

### Create Rule
User: "Archive newsletters older than 7 days"
- Skill parses natural language into structured rule
- Saves via `create_rule`
- Offers dry-run preview

### Run Automation
User: "Run my email rules"
- Executes all enabled rules
- Reports actions taken

## File Structure

```
# MCP Server (this repo)
src/email_assistant/
├── server.py           # MCP server entry point
├── gmail/
│   ├── auth.py         # OAuth2
│   ├── client.py       # Gmail API wrapper
│   └── models.py       # Email, Thread, Label
├── triage/
│   ├── scorer.py       # Priority scoring
│   └── categorizer.py  # Email categorization
├── rules/
│   ├── models.py       # Rule, Condition, Action
│   ├── parser.py       # Natural language parsing
│   └── engine.py       # Rule execution
└── storage/
    └── db.py           # SQLite storage

# Gmail Skill (installed globally)
~/.claude/skills/gmail/
├── SKILL.md            # Main skill file
├── TRIAGE.md           # Triage workflow
├── AUTOMATION.md       # Rule management
└── PRIORITIZATION.md   # Criteria schema
```

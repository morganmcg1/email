# Email Assistant

## Overview

This is a Gmail MCP server with an accompanying Claude Code skill for intelligent email management.

**Architecture:**
- `src/email_assistant/` - MCP server providing raw Gmail API operations
- `~/.claude/skills/gmail/` - Claude Code skill for orchestration and state management
- `~/.email-assistant/credentials.json` - Gmail API credentials

## Components

### MCP Server

The server provides raw Gmail operations via MCP tools:

**Core Email Tools:**
- `get_emails`, `search_emails`, `get_email`, `get_thread`
- `archive_email`, `trash_email`, `mark_read`
- `modify_labels`, `batch_label`, `list_labels`

**Auth Tools:**
- `authenticate`, `check_auth`

### Gmail Skill

Installed globally at `~/.claude/skills/gmail/`, this skill:
- Manages state (prioritization criteria, automation rules) as JSON files
- Handles triage logic (scoring emails HIGH/MEDIUM/LOW)
- Parses natural language into automation rules
- Spawns subagents for email processing (context management)

**State files:**
- `~/.claude/skills/gmail/prioritization.json` - User's priority criteria
- `~/.claude/skills/gmail/rules.json` - Automation rules

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
- Skill checks for criteria in `~/.claude/skills/gmail/prioritization.json`
- If no criteria: Skill runs interview to gather preferences and saves them
- Spawns subagent to fetch emails and score them using the criteria
- Returns prioritized list (HIGH/MEDIUM/LOW)

### Create Rule
User: "Archive newsletters older than 7 days"
- Skill parses natural language into structured rule
- Saves to `~/.claude/skills/gmail/rules.json`
- Offers dry-run preview

### Run Automation
User: "Run my email rules"
- Loads rules from `~/.claude/skills/gmail/rules.json`
- Executes matching emails via MCP tools
- Reports actions taken

## File Structure

```
# MCP Server (this repo)
src/email_assistant/
├── server.py           # MCP server entry point
└── gmail/
    ├── auth.py         # OAuth2
    ├── client.py       # Gmail API wrapper
    └── models.py       # Email, Thread, Label

# Gmail Skill (installed globally)
~/.claude/skills/gmail/
├── SKILL.md            # Main skill file
├── TRIAGE.md           # Triage workflow
├── AUTOMATION.md       # Rule management
├── PRIORITIZATION.md   # Criteria schema
├── prioritization.json # User's priority criteria (created on first triage)
└── rules.json          # Automation rules (created when first rule added)
```

---

## grv - a git worktree helper
This project also leverages the `grv` library to mangage git worktrees so that agent-driven software development can be managed  - https://github.com/tssweeney/grv

When adding or reviewing new features consider whether or not to use `grv` or whether you already are in a `grv` workspace. When finished with feature development you can use `grv` to also cleanup unneeded worktrees. See the repo documentation for full usage instructions.

## User Clarifications

### Interviewing the developer about how to do a task:
When asked for a large piece of work which seems vague or needs clarification, please interview me in detail using the AskUserQuestionTool about literally anything: technical implementation, UI & UX, concerns, tradeoffs, etc. but make sure the questions are not obvious. Be very in-depth and continue interviewing me continually until it's complete, then write the learnings to README.md

## Coding guidelines and philosophy
- You should generate code that is simple and redable, avoid unnecesary abstractions and complexity. This is a research codebase so we want to be mantainable and readable.
- Avoid overly defensive coding, no need for a lot of `try, except` patterns, I want the code to fail is something is wrong so that i can fix it.
- Do not add demo-only flags or placeholder CLI options that gate real functionality (e.g., `--run` just to toggle execution); scripts should run their main logic directly.
- Adhere to python 3.12+ conventions


### Code Review

After finishing a code review, always check the diff against main, and remove all AI generated slop introduced in this branch.

This includes:
- Extra comments that a human wouldn't add or is inconsistent with the rest of the file
- Variables that are used a single time right after declaration, prefer inlining the rhs
- Extra defensive checks or try/catch blocks that are abnormal for that area of the codebase (especially if called by trusted / validated codepaths)
- Casts to any to get around type issues
- Any other style that is inconsistent with the file

Report at the end with only a 1-3 sentence summary of what you changed

### Testing
- When running tests, default to not mocking components in the system, assume we want full end-to-end testing, including live API calls, in every test. Clarify with the user if you feel that mocking would be the better solution.

### Dependency management
This project uses uv as dependency manager for python. Run scripts using `uv run script.py` instead of calling pythong directly. This is also true for tools like `uv run pytest`

### Argument parsing
Use `simple_parsing` as an argument paraser for the scripts. Like this

```python
import simple_parsing as sp

@dataclass
class Args:
    """ Help string for this group of command-line arguments """
    arg1: str       # Help string for a required str argument
    arg2: int = 1   # Help string for arg2

args = sp.parse(Args)
```

## Typing
We are using modern python (3.12+) so no need to import annotations, you can also use `dict` and `list` and `a | b` or `a | None` instead of Optional, Union, Dict, List, etc...

## Environment Variables
- Use a .env file for all env vars
- Use `python-dotenv` to load these env vars

## Printing and logging
Use rich.Console to print stuff on scripts, use Panel and console.rule to make stuff organized

## Debugging
When running scripts, use the `debug` flags if avaliable, and ask to run the full pipeline (this enables faster iteration)

## Running Analysis
Ensure to always use performant code for runnning analysis, always use pandas best practices for speed and efficiency.

## Wroking with Weights & Biases - project and entity to use
When logging to `wandb` or `weave` from Weigths & Biases, always log to the `milieu` entity and the `radio_analysis` project, unless specifically asked to log elsewhere

## Working with Jupyter notebooks
### Reading / visualing pandas dataframes
When working with jupyter notebooks, remove truncation so we can print full outputs
```python
import pandas as pd
pd.set_option('display.max_columns', None)   # no column truncation
pd.set_option('display.width', None)         # keep each row on one line
pd.set_option('display.max_colwidth', None)  # don't truncate long string cells
```

### Autoreload
Prefer adding autoreload at the top cell of the notebook so that we don't have to restart the notebook when we make changes to our library
```python
%load_ext autoreload
%autoreload 2
```

## Running commands
Avoid asking the user to run commands unless its strictly necesary for the user to run it. Its fine to educate them and tell them the commands that are being run and why, but if you've been asked to achieve a task and there isn't a strong reason why you can't just run the command yourself, just run the command.

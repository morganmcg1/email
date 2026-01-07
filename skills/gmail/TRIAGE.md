# Email Triage Workflow

## Overview

Triage scores emails as HIGH, MEDIUM, or LOW priority based on user-defined criteria stored in `~/.claude/skills/gmail/prioritization.json`.

## Step 1: Check for Existing Criteria

Read `~/.claude/skills/gmail/prioritization.json` to see if the user has set up their preferences.

```python
import json
from pathlib import Path

criteria_path = Path.home() / ".claude/skills/gmail/prioritization.json"
if criteria_path.exists():
    criteria = json.loads(criteria_path.read_text())
else:
    criteria = None
```

**If criteria exist:** Proceed to Step 3.
**If no criteria:** Proceed to Step 2.

## Step 2: Interview for Prioritization Criteria

Ask the user these questions to build their priority profile:

### Questions to Ask

1. **VIP Senders**
   "Who are the people whose emails should always be high priority? (e.g., boss, key clients, family)"
   → Store as email addresses in `vip_senders`

2. **Important Domains**
   "Are there any domains that should always be high priority? (e.g., your company domain, key partners)"
   → Store in `vip_domains`

3. **Urgency Keywords**
   "What words in a subject line signal something is urgent? (e.g., 'urgent', 'ASAP', 'deadline')"
   → Store in `high_priority_keywords`

4. **Low Priority Types**
   "What types of emails are low priority for you? (e.g., newsletters, promotional, social notifications)"
   → Store in `low_priority_types`

5. **Custom Rules** (optional)
   "Any other rules? (e.g., 'Emails about Project X are always high priority')"
   → Store in `custom_rules`

### Save Criteria

After gathering responses, save to JSON:

```python
import json
from pathlib import Path

criteria = {
    "vip_senders": ["boss@company.com", "client@important.com"],
    "vip_domains": ["company.com", "partner.org"],
    "high_priority_keywords": ["urgent", "ASAP", "deadline", "action required"],
    "low_priority_types": ["newsletter", "promotional", "marketing", "social"],
    "custom_rules": ["Project X emails are high priority"]
}

criteria_path = Path.home() / ".claude/skills/gmail/prioritization.json"
criteria_path.write_text(json.dumps(criteria, indent=2))
```

## Step 3: Triage Emails via Claude Code Subagent

**Important:** Use a subagent to avoid bloating main context with email content.

### Claude Code Subagent Prompt Template

```
Use Gmail MCP tools to triage the inbox.

1. Filtering: If the user hasn't specified a time-frame, ask them over what timeframe you should filter unread emails by
2. Read prioritization criteria from ~/.claude/skills/gmail/prioritization.json
3. Call get_emails with unread_only=true, max_results=20
4. Score each email as HIGH, MEDIUM, or LOW based on:

   HIGH if:
   - Sender is in VIP list: {vip_senders}
   - Sender domain is: {vip_domains}
   - Subject/body contains: {high_priority_keywords}

   LOW if:
   - Email type matches: {low_priority_types}
   - Appears to be newsletter/promotional

   MEDIUM: Everything else

5. For each email, also determine if it NEEDS REPLY:
   - NEEDS REPLY if: contains question, requests action, awaits user input
   - NO REPLY if: informational, CC'd only, automated/transactional

6. Return a prioritized list with ONLY:
   - Priority level (HIGH/MEDIUM/LOW)
   - [REPLY NEEDED] flag if applicable
   - Sender name
   - Subject line
   - One sentence summary

Do NOT include full email bodies in response.
```

## Step 4: Present Results

Format the results clearly, including:
- Priority level (HIGH/MEDIUM/LOW)
- **[REPLY NEEDED]** flag for emails requiring response
- One-sentence summary for each email

```
## Inbox Triage Results

### HIGH Priority (3)
- [HIGH] [REPLY NEEDED] CEO <ceo@company.com>: Q4 Budget Review Needed
  Summary: Requesting budget review before Friday meeting. Asks for your input on Q4 projections.

- [HIGH] [REPLY NEEDED] Client <john@client.com>: Contract Question
  Summary: Question about renewal terms - needs clarification on pricing tier.

- [HIGH] Team Lead <lead@company.com>: Production Incident
  Summary: Alert about server outage, already being handled by on-call.

### MEDIUM Priority (5)
- [MEDIUM] [REPLY NEEDED] Team <team@company.com>: Project Update Request
  Summary: Asking for status update on your deliverables.

- [MEDIUM] Team <team@company.com>: Standup Notes
  Summary: Yesterday's standup summary - informational only.

### LOW Priority (8)
- [LOW] Newsletter <news@techsite.com>: Weekly Digest
  Summary: Tech news roundup.

- [LOW] LinkedIn: New connection request
  Summary: Connection request from recruiter.
```

### Reply Detection Criteria

Mark as **[REPLY NEEDED]** if:
- Contains a direct question to the user
- Requests action or confirmation
- Part of conversation awaiting user input
- Sender explicitly waiting on user

Do NOT mark as reply needed if:
- Informational only (newsletters, notifications)
- CC'd only, not direct recipient
- Automated/transactional emails

## Re-triaging

User can ask to re-triage at any time. Always use fresh email data.

## Updating Criteria

If user says things like "Actually, emails from X should be high priority", update their criteria:
1. Read current criteria from `~/.claude/skills/gmail/prioritization.json`
2. Add the new rule
3. Save updated criteria back to the file

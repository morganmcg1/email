# Prioritization Criteria Schema

## Overview

User prioritization criteria determine how emails are scored as HIGH, MEDIUM, or LOW.

## Schema

```json
{
  "vip_senders": ["email@example.com", ...],
  "vip_domains": ["company.com", ...],
  "high_priority_keywords": ["urgent", "ASAP", ...],
  "low_priority_types": ["newsletter", "promotional", ...],
  "custom_rules": ["Any email about Project X is high priority", ...]
}
```

## Fields

### vip_senders
Email addresses that are always HIGH priority.

**Examples:**
- `boss@company.com`
- `ceo@company.com`
- `spouse@gmail.com`
- `key.client@customer.com`

### vip_domains
Domains where all emails are HIGH priority.

**Examples:**
- `company.com` (your employer)
- `importantclient.com`
- `partner.org`

### high_priority_keywords
Words in subject or body that signal HIGH priority.

**Common examples:**
- `urgent`
- `ASAP`
- `deadline`
- `action required`
- `time sensitive`
- `critical`
- `immediate`

### low_priority_types
Email types that are LOW priority.

**Common examples:**
- `newsletter`
- `promotional`
- `marketing`
- `social` (LinkedIn, Twitter notifications)
- `digest`
- `weekly update`
- `noreply`

### custom_rules
Free-form rules in plain English for special cases.

- Calendar acceptance/reject emails from @wandb.com or @coreweave.com emails are NOT high priority.

## Scoring Logic

```
1. Check vip_senders → HIGH if match
2. Check vip_domains → HIGH if match
3. Check high_priority_keywords → HIGH if found in subject/body
4. Check low_priority_types → LOW if email type matches
5. Apply custom_rules → Override based on rule
6. Default → MEDIUM
```

## Example Configurations

### Busy Executive
```json
{
  "vip_senders": ["ceo@company.com", "board@company.com"],
  "vip_domains": ["company.com"],
  "high_priority_keywords": ["urgent", "board meeting", "investor"],
  "low_priority_types": ["newsletter", "promotional", "social"],
  "custom_rules": []
}
```

### Freelancer
```json
{
  "vip_senders": [],
  "vip_domains": ["client1.com", "client2.com", "client3.com"],
  "high_priority_keywords": ["invoice", "payment", "deadline", "contract"],
  "low_priority_types": ["newsletter", "promotional"],
  "custom_rules": ["Emails about active projects are high priority"]
}
```

### Developer
```json
{
  "vip_senders": ["manager@company.com"],
  "vip_domains": ["company.com"],
  "high_priority_keywords": ["production", "outage", "incident", "P0"],
  "low_priority_types": ["newsletter", "promotional", "recruiting"],
  "custom_rules": [
    "GitHub notifications for my repos are medium priority",
    "CI/CD failure notifications are high priority"
  ]
}
```

## Updating Criteria

To update criteria without losing existing settings:

1. Get current: `get_prioritization_criteria()`
2. Modify the relevant field
3. Save: `setup_prioritization(...all fields...)`

Or simply call `setup_prioritization` with all fields (it replaces existing).

## Clearing Criteria

To start fresh: `clear_prioritization()`

This removes all criteria and will trigger the interview flow on next triage.

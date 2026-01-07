# Email Automation Rules

## Overview

Automation rules let users define conditions and actions that run automatically on their inbox.

## Creating Rules

### From Natural Language

User says: "Archive newsletters older than 7 days"

1. Parse into structured format:
   ```json
   {
     "conditions": {
       "category": "newsletter",
       "age": ">7d"
     },
     "actions": ["archive"]
   }
   ```

2. Save via MCP:
   ```
   create_rule(
     name="Archive old newsletters",
     natural_language="Archive newsletters older than 7 days",
     conditions={"category": "newsletter", "age": ">7d"},
     actions={"type": "archive"}
   )
   ```

### Common Rule Patterns

| User Request | Conditions | Actions |
|--------------|------------|---------|
| "Archive newsletters older than a week" | category=newsletter, age>7d | archive |
| "Star emails from my boss" | sender=boss@company.com | star |
| "Mark promotional emails as read" | category=promotional | mark_read |
| "Trash emails from noreply addresses" | sender contains "noreply" | trash |
| "Label emails from clients as Important" | domain in [client1.com, client2.com] | add_label=Important |

## Condition Types

| Field | Operators | Example |
|-------|-----------|---------|
| `sender` | equals, contains | sender equals "boss@company.com" |
| `sender_domain` | equals, in_list | sender_domain in ["company.com"] |
| `subject` | contains, starts_with | subject contains "urgent" |
| `labels` | contains | labels contains "INBOX" |
| `date` | older_than, newer_than | date older_than 7d |
| `has_attachment` | equals | has_attachment equals true |
| `is_unread` | equals | is_unread equals true |

## Action Types

| Action | Description | Params |
|--------|-------------|--------|
| `archive` | Remove from inbox | - |
| `trash` | Move to trash | - |
| `delete` | Permanently delete | - |
| `mark_read` | Mark as read | - |
| `mark_unread` | Mark as unread | - |
| `star` | Add star | - |
| `unstar` | Remove star | - |
| `add_label` | Add a label | label name |
| `remove_label` | Remove a label | label name |

## Running Automation

### Preview First (Recommended)

Always offer a dry-run before executing:

```
run_automation(dry_run=true, max_emails=50)
```

This shows what WOULD happen without making changes.

### Execute

```
run_automation(max_emails=100)
```

### Present Results

```
## Automation Results

Rule: Archive old newsletters
  - TechCrunch Weekly Digest... [WOULD] archive
  - Morning Brew #423... [WOULD] archive

Rule: Star emails from boss
  - Q4 Planning... [WOULD] star

Summary: 3 emails matched, 3 actions would be taken
```

## Managing Rules

### List Rules
```
list_rules()
```

### Delete Rule
```
delete_rule(rule_id=1)
```

### Disable/Enable
Rules can be toggled without deleting. (Future: implement toggle_rule)

## Best Practices

1. **Always dry-run first** - Show preview before executing
2. **Be conservative with destructive actions** - Prefer archive over delete
3. **Confirm understanding** - Restate the rule before saving
4. **Test with small batches** - Use max_emails=10 for testing

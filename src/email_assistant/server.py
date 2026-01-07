"""MCP server for email assistant."""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .gmail import GmailClient
from .gmail.models import Priority
from .rules.engine import RuleEngine
from .rules.models import Rule, RuleAction, RuleCondition
from .storage import Database
from .storage.db import PrioritizationCriteria

server = Server("email-assistant")
gmail_client: GmailClient | None = None
db: Database | None = None


def get_gmail() -> GmailClient:
    global gmail_client
    if gmail_client is None:
        gmail_client = GmailClient()
    return gmail_client


def get_db() -> Database:
    global db
    if db is None:
        db = Database()
    return db


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        # Auth
        Tool(
            name="authenticate",
            description="Authenticate with Gmail. Run this first if not authenticated.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="check_auth",
            description="Check if authenticated with Gmail.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # Core email tools
        Tool(
            name="get_emails",
            description="Fetch emails from inbox with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query (e.g., 'from:boss@company.com')",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of emails to return",
                        "default": 20,
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only return unread emails",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="search_emails",
            description="Search emails using Gmail query syntax.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Gmail search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results",
                        "default": 20,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_email",
            description="Get a single email by ID with full content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "Email message ID"},
                },
                "required": ["email_id"],
            },
        ),
        Tool(
            name="get_thread",
            description="Get an email thread with all messages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "Thread ID"},
                },
                "required": ["thread_id"],
            },
        ),
        Tool(
            name="modify_labels",
            description="Add or remove labels from an email.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "Email message ID"},
                    "add_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add",
                    },
                    "remove_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to remove",
                    },
                },
                "required": ["email_id"],
            },
        ),
        Tool(
            name="archive_email",
            description="Archive one or more emails (remove from inbox).",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_ids": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Email ID(s) to archive",
                    },
                },
                "required": ["email_ids"],
            },
        ),
        Tool(
            name="trash_email",
            description="Move one or more emails to trash.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_ids": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "Email ID(s) to trash",
                    },
                },
                "required": ["email_ids"],
            },
        ),
        Tool(
            name="batch_label",
            description="Add or remove labels from multiple emails at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email IDs to modify",
                    },
                    "add_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to add",
                    },
                    "remove_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to remove",
                    },
                },
                "required": ["email_ids"],
            },
        ),
        Tool(
            name="mark_read",
            description="Mark email as read.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {"type": "string", "description": "Email message ID"},
                },
                "required": ["email_id"],
            },
        ),
        Tool(
            name="list_labels",
            description="List all Gmail labels.",
            inputSchema={"type": "object", "properties": {}},
        ),
        # Triage tools
        Tool(
            name="setup_prioritization",
            description="Set up email prioritization criteria through an interview. Call this to define what makes emails high/medium/low priority for you.",
            inputSchema={
                "type": "object",
                "properties": {
                    "vip_senders": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses of VIP senders (always high priority)",
                    },
                    "vip_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Domains that should be high priority (e.g., 'company.com')",
                    },
                    "high_priority_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Keywords in subject/body that signal high priority",
                    },
                    "low_priority_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of emails that are low priority (e.g., 'newsletter', 'promotional')",
                    },
                    "custom_rules": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Custom rules in plain English for prioritization",
                    },
                },
            },
        ),
        Tool(
            name="get_prioritization_criteria",
            description="Get current prioritization criteria. Returns null if not set up yet.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="clear_prioritization",
            description="Clear all prioritization criteria to start fresh.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="triage_inbox",
            description="Triage unread emails and assign priority levels (high/medium/low). If no prioritization criteria exist, you should first call setup_prioritization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_emails": {
                        "type": "integer",
                        "description": "Maximum emails to triage",
                        "default": 20,
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only triage unread emails",
                        "default": True,
                    },
                },
            },
        ),
        # Automation tools
        Tool(
            name="create_rule",
            description="Create an automation rule from natural language or structured conditions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Rule name"},
                    "natural_language": {
                        "type": "string",
                        "description": "Rule in plain English (e.g., 'Archive newsletters older than 7 days')",
                    },
                    "conditions": {
                        "type": "object",
                        "description": "Structured conditions (alternative to natural_language)",
                    },
                    "actions": {
                        "type": "object",
                        "description": "Structured actions (alternative to natural_language)",
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_rules",
            description="List all automation rules.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_disabled": {
                        "type": "boolean",
                        "description": "Include disabled rules",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="delete_rule",
            description="Delete an automation rule.",
            inputSchema={
                "type": "object",
                "properties": {
                    "rule_id": {"type": "integer", "description": "Rule ID to delete"},
                },
                "required": ["rule_id"],
            },
        ),
        Tool(
            name="run_automation",
            description="Execute all enabled automation rules on inbox.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "description": "If true, show what would happen without making changes",
                        "default": False,
                    },
                    "max_emails": {
                        "type": "integer",
                        "description": "Maximum emails to process",
                        "default": 100,
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        result = await _handle_tool(name, arguments)
        return [TextContent(type="text", text=str(result))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]


async def _handle_tool(name: str, args: dict[str, Any]) -> Any:
    """Route tool calls to implementations."""
    gmail = get_gmail()
    database = get_db()

    # Auth tools
    if name == "authenticate":
        gmail.authenticate()
        profile = gmail.get_profile()
        return f"Authenticated as {profile.get('emailAddress')}"

    if name == "check_auth":
        if gmail.auth.is_authenticated():
            profile = gmail.get_profile()
            return f"Authenticated as {profile.get('emailAddress')}"
        return "Not authenticated. Call 'authenticate' tool first."

    # Core email tools
    if name == "get_emails":
        emails = gmail.get_emails(
            query=args.get("query", ""),
            max_results=args.get("max_results", 20),
            unread_only=args.get("unread_only", False),
        )
        return _format_email_list(emails)

    if name == "search_emails":
        emails = gmail.search_emails(
            query=args["query"],
            max_results=args.get("max_results", 20),
        )
        return _format_email_list(emails)

    if name == "get_email":
        email = gmail.get_email(args["email_id"])
        if email:
            return _format_email_detail(email)
        return "Email not found"

    if name == "get_thread":
        thread = gmail.get_thread(args["thread_id"])
        if thread:
            return _format_thread(thread)
        return "Thread not found"

    if name == "modify_labels":
        success = gmail.modify_labels(
            args["email_id"],
            add_labels=args.get("add_labels"),
            remove_labels=args.get("remove_labels"),
        )
        return "Labels modified" if success else "Failed to modify labels"

    if name == "archive_email":
        email_ids = args["email_ids"]
        if isinstance(email_ids, str):
            email_ids = [email_ids]
        results = gmail.archive_emails(email_ids)
        success_count = sum(1 for v in results.values() if v)
        return f"Archived {success_count}/{len(email_ids)} emails"

    if name == "trash_email":
        email_ids = args["email_ids"]
        if isinstance(email_ids, str):
            email_ids = [email_ids]
        success_count = 0
        for eid in email_ids:
            if gmail.trash_email(eid):
                success_count += 1
        return f"Trashed {success_count}/{len(email_ids)} emails"

    if name == "batch_label":
        email_ids = args["email_ids"]
        add_labels = args.get("add_labels")
        remove_labels = args.get("remove_labels")
        success_count = 0
        for eid in email_ids:
            if gmail.modify_labels(eid, add_labels=add_labels, remove_labels=remove_labels):
                success_count += 1
        return f"Modified labels on {success_count}/{len(email_ids)} emails"

    if name == "mark_read":
        success = gmail.mark_read(args["email_id"])
        return "Marked as read" if success else "Failed to mark as read"

    if name == "list_labels":
        labels = gmail.list_labels()
        return "\n".join(f"- {l.name} ({l.id})" for l in labels)

    # Triage tools
    if name == "setup_prioritization":
        criteria = PrioritizationCriteria(
            vip_senders=args.get("vip_senders", []),
            vip_domains=args.get("vip_domains", []),
            high_priority_keywords=args.get("high_priority_keywords", []),
            low_priority_types=args.get("low_priority_types", []),
            custom_rules=args.get("custom_rules", []),
        )
        database.save_prioritization_criteria(criteria)
        return f"Prioritization criteria saved:\n{_format_criteria(criteria)}"

    if name == "get_prioritization_criteria":
        criteria = database.get_prioritization_criteria()
        if criteria:
            return _format_criteria(criteria)
        return "No prioritization criteria set. Use 'setup_prioritization' to define your preferences."

    if name == "clear_prioritization":
        database.clear_prioritization_criteria()
        return "Prioritization criteria cleared."

    if name == "triage_inbox":
        criteria = database.get_prioritization_criteria()
        if not criteria:
            return (
                "No prioritization criteria found. Before triaging, please set up your "
                "prioritization preferences by calling 'setup_prioritization' with:\n"
                "- vip_senders: Email addresses that are always high priority\n"
                "- vip_domains: Domains that should be high priority\n"
                "- high_priority_keywords: Keywords that signal urgency\n"
                "- low_priority_types: Types of emails that are low priority\n"
                "- custom_rules: Any other rules in plain English"
            )

        emails = gmail.get_emails(
            max_results=args.get("max_emails", 20),
            unread_only=args.get("unread_only", True),
        )

        triaged = _triage_emails(emails, criteria)
        return _format_triaged_emails(triaged)

    # Automation tools
    if name == "create_rule":
        conditions = args.get("conditions", {})
        actions = args.get("actions", {})
        natural_lang = args.get("natural_language")

        if natural_lang and not conditions:
            conditions = {"natural_language": natural_lang}
            actions = {"parsed": False}

        rule_id = database.save_rule(
            name=args["name"],
            conditions=conditions,
            actions=actions,
            natural_language=natural_lang,
        )
        return f"Rule created with ID {rule_id}"

    if name == "list_rules":
        rules = database.get_rules(enabled_only=not args.get("include_disabled", False))
        if not rules:
            return "No rules defined."
        return "\n\n".join(_format_rule(r) for r in rules)

    if name == "delete_rule":
        success = database.delete_rule(args["rule_id"])
        return "Rule deleted" if success else "Rule not found"

    if name == "run_automation":
        rule_dicts = database.get_rules(enabled_only=True)
        if not rule_dicts:
            return "No enabled rules to run."

        dry_run = args.get("dry_run", False)
        max_emails = args.get("max_emails", 100)

        # Convert dict rules to Rule objects
        rules = []
        for rd in rule_dicts:
            conditions = [
                RuleCondition(**c) for c in rd.get("conditions", [])
                if isinstance(c, dict) and "field" in c
            ]
            actions = [
                RuleAction(**a) for a in rd.get("actions", [])
                if isinstance(a, dict) and "action_type" in a
            ]
            rules.append(Rule(
                id=rd.get("id"),
                name=rd["name"],
                natural_language=rd.get("natural_language"),
                conditions=conditions,
                actions=actions,
                enabled=rd.get("enabled", True),
            ))

        # Fetch emails to run rules against
        emails = gmail.get_emails(max_results=max_emails)
        if not emails:
            return "No emails to process."

        # Execute rules
        engine = RuleEngine(gmail)
        results = engine.execute_rules(rules, emails, dry_run=dry_run)

        return _format_automation_results(results, dry_run)

    return f"Unknown tool: {name}"


def _format_email_list(emails: list) -> str:
    """Format list of emails for display."""
    if not emails:
        return "No emails found."

    lines = []
    for e in emails:
        status = "[UNREAD] " if e.is_unread else ""
        star = "[*] " if e.is_starred else ""
        lines.append(f"{status}{star}{e.sender}: {e.subject}")
        lines.append(f"  ID: {e.id} | Date: {e.date.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"  {e.snippet[:100]}...")
        lines.append("")

    return "\n".join(lines)


def _format_email_detail(email) -> str:
    """Format single email for detailed view."""
    body = email.body_text or email.body_html or email.snippet
    if len(body) > 2000:
        body = body[:2000] + "..."

    return f"""From: {email.sender} <{email.sender_email}>
To: {', '.join(email.recipients)}
Subject: {email.subject}
Date: {email.date.strftime('%Y-%m-%d %H:%M')}
Labels: {', '.join(email.labels)}
Attachments: {len(email.attachments)}

{body}"""


def _format_thread(thread) -> str:
    """Format email thread."""
    lines = [f"Thread: {thread.subject}", f"Messages: {thread.message_count}", ""]
    for msg in thread.messages:
        lines.append(f"--- {msg.sender} ({msg.date.strftime('%Y-%m-%d %H:%M')}) ---")
        body = msg.body_text or msg.snippet
        if len(body) > 500:
            body = body[:500] + "..."
        lines.append(body)
        lines.append("")
    return "\n".join(lines)


def _format_criteria(criteria: PrioritizationCriteria) -> str:
    """Format prioritization criteria."""
    lines = ["Prioritization Criteria:"]
    if criteria.vip_senders:
        lines.append(f"  VIP Senders: {', '.join(criteria.vip_senders)}")
    if criteria.vip_domains:
        lines.append(f"  VIP Domains: {', '.join(criteria.vip_domains)}")
    if criteria.high_priority_keywords:
        lines.append(f"  High Priority Keywords: {', '.join(criteria.high_priority_keywords)}")
    if criteria.low_priority_types:
        lines.append(f"  Low Priority Types: {', '.join(criteria.low_priority_types)}")
    if criteria.custom_rules:
        lines.append("  Custom Rules:")
        for rule in criteria.custom_rules:
            lines.append(f"    - {rule}")
    return "\n".join(lines)


def _format_rule(rule: dict) -> str:
    """Format automation rule."""
    status = "enabled" if rule["enabled"] else "disabled"
    return f"""Rule #{rule['id']}: {rule['name']} ({status})
  {rule.get('natural_language') or 'Structured rule'}
  Conditions: {rule['conditions']}
  Actions: {rule['actions']}"""


def _triage_emails(emails: list, criteria: PrioritizationCriteria) -> list[dict]:
    """Triage emails based on criteria."""
    triaged = []
    for email in emails:
        priority = _score_email(email, criteria)
        triaged.append({"email": email, "priority": priority})

    # Sort by priority (high first)
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    triaged.sort(key=lambda x: priority_order.get(x["priority"], 2))

    return triaged


def _score_email(email, criteria: PrioritizationCriteria) -> Priority:
    """Score a single email based on criteria."""
    # Check VIP senders
    if email.sender_email in criteria.vip_senders:
        return Priority.HIGH

    # Check VIP domains
    sender_domain = email.sender_email.split("@")[-1] if "@" in email.sender_email else ""
    if sender_domain in criteria.vip_domains:
        return Priority.HIGH

    # Check high priority keywords
    text = f"{email.subject} {email.snippet}".lower()
    for keyword in criteria.high_priority_keywords:
        if keyword.lower() in text:
            return Priority.HIGH

    # Check low priority types
    for low_type in criteria.low_priority_types:
        low_type_lower = low_type.lower()
        if low_type_lower in text or low_type_lower in email.sender.lower():
            return Priority.LOW

    # Default to medium
    return Priority.MEDIUM


def _format_triaged_emails(triaged: list[dict]) -> str:
    """Format triaged email list."""
    if not triaged:
        return "No emails to triage."

    lines = ["Triaged Emails:", ""]
    for item in triaged:
        email = item["email"]
        priority = item["priority"].value.upper()
        lines.append(f"[{priority}] {email.sender}: {email.subject}")
        lines.append(f"       ID: {email.id}")
        lines.append("")

    return "\n".join(lines)


def _format_automation_results(results: dict, dry_run: bool) -> str:
    """Format automation execution results."""
    if not results:
        return "No rules matched any emails."

    mode = "DRY RUN - " if dry_run else ""
    lines = [f"{mode}Automation Results:", ""]

    total_matched = 0
    total_actions = 0

    for rule_name, rule_results in results.items():
        lines.append(f"Rule: {rule_name}")
        for r in rule_results:
            total_matched += 1
            lines.append(f"  - {r['subject'][:50]}...")
            for action in r.get("actions", []):
                total_actions += 1
                if dry_run:
                    lines.append(f"    [WOULD] {action['action']}")
                else:
                    status = "OK" if action.get("success") else "FAILED"
                    lines.append(f"    [{status}] {action['action']}")
        lines.append("")

    lines.append(f"Summary: {total_matched} emails matched, {total_actions} actions {'would be taken' if dry_run else 'taken'}")
    return "\n".join(lines)


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()

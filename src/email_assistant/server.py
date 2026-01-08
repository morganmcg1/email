"""MCP server for email assistant.

This server provides raw Gmail API operations via MCP tools.
State management (prioritization criteria, automation rules) is handled
by the Claude Code skill at ~/.claude/skills/gmail/.
"""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .gmail import GmailClient

server = Server("email-assistant")
gmail_client: GmailClient | None = None


def get_gmail() -> GmailClient:
    global gmail_client
    if gmail_client is None:
        gmail_client = GmailClient()
    return gmail_client


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
                        "default": 200,
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
                        "default": 200,
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
            max_results=args.get("max_results", 200),
            unread_only=args.get("unread_only", False),
        )
        return _format_email_list(emails)

    if name == "search_emails":
        emails = gmail.search_emails(
            query=args["query"],
            max_results=args.get("max_results", 200),
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


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()

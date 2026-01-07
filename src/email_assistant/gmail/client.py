"""Gmail API client wrapper."""

import base64
from datetime import datetime
from email.utils import parseaddr, parsedate_to_datetime
from typing import Optional

from googleapiclient.discovery import build

from .auth import GmailAuth
from .models import Attachment, Email, EmailThread, Label


class GmailClient:
    """High-level Gmail API client."""

    def __init__(self, auth: Optional[GmailAuth] = None):
        self.auth = auth or GmailAuth()
        self._service = None

    @property
    def service(self):
        """Lazy-load Gmail API service."""
        if self._service is None:
            creds = self.auth.get_credentials()
            if creds is None:
                raise RuntimeError("Not authenticated. Call authenticate() first.")
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def authenticate(self) -> None:
        """Run OAuth flow if not authenticated."""
        if not self.auth.is_authenticated():
            self.auth.authenticate()
            self._service = None  # Reset to pick up new credentials

    def get_profile(self) -> dict:
        """Get user's Gmail profile."""
        return self.service.users().getProfile(userId="me").execute()

    def list_labels(self) -> list[Label]:
        """List all Gmail labels."""
        results = self.service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])
        return [Label(id=l["id"], name=l["name"], type=l.get("type", "user")) for l in labels]

    def get_emails(
        self,
        query: str = "",
        max_results: int = 50,
        unread_only: bool = False,
        label_ids: Optional[list[str]] = None,
    ) -> list[Email]:
        """Fetch emails matching query."""
        if unread_only:
            query = f"is:unread {query}".strip()

        params = {"userId": "me", "maxResults": max_results}
        if query:
            params["q"] = query
        if label_ids:
            params["labelIds"] = label_ids

        results = self.service.users().messages().list(**params).execute()
        messages = results.get("messages", [])

        emails = []
        for msg in messages:
            email = self.get_email(msg["id"])
            if email:
                emails.append(email)

        return emails

    def get_email(self, message_id: str) -> Optional[Email]:
        """Get full email by ID."""
        try:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return self._parse_message(msg)
        except Exception:
            return None

    def search_emails(self, query: str, max_results: int = 50) -> list[Email]:
        """Search emails using Gmail query syntax."""
        return self.get_emails(query=query, max_results=max_results)

    def get_thread(self, thread_id: str) -> Optional[EmailThread]:
        """Get full email thread."""
        try:
            thread = (
                self.service.users()
                .threads()
                .get(userId="me", id=thread_id, format="full")
                .execute()
            )
            messages = [self._parse_message(m) for m in thread.get("messages", [])]
            messages = [m for m in messages if m is not None]

            return EmailThread(
                id=thread_id,
                subject=messages[0].subject if messages else "",
                messages=messages,
                snippet=thread.get("snippet", ""),
            )
        except Exception:
            return None

    def modify_labels(
        self,
        message_id: str,
        add_labels: Optional[list[str]] = None,
        remove_labels: Optional[list[str]] = None,
    ) -> bool:
        """Add or remove labels from an email."""
        try:
            body = {}
            if add_labels:
                body["addLabelIds"] = add_labels
            if remove_labels:
                body["removeLabelIds"] = remove_labels

            self.service.users().messages().modify(
                userId="me", id=message_id, body=body
            ).execute()
            return True
        except Exception:
            return False

    def archive_email(self, message_id: str) -> bool:
        """Archive an email (remove INBOX label)."""
        return self.modify_labels(message_id, remove_labels=["INBOX"])

    def archive_emails(self, message_ids: list[str]) -> dict[str, bool]:
        """Archive multiple emails."""
        return {msg_id: self.archive_email(msg_id) for msg_id in message_ids}

    def mark_read(self, message_id: str) -> bool:
        """Mark email as read."""
        return self.modify_labels(message_id, remove_labels=["UNREAD"])

    def mark_unread(self, message_id: str) -> bool:
        """Mark email as unread."""
        return self.modify_labels(message_id, add_labels=["UNREAD"])

    def star_email(self, message_id: str) -> bool:
        """Star an email."""
        return self.modify_labels(message_id, add_labels=["STARRED"])

    def unstar_email(self, message_id: str) -> bool:
        """Remove star from email."""
        return self.modify_labels(message_id, remove_labels=["STARRED"])

    def trash_email(self, message_id: str) -> bool:
        """Move email to trash."""
        try:
            self.service.users().messages().trash(userId="me", id=message_id).execute()
            return True
        except Exception:
            return False

    def delete_email(self, message_id: str) -> bool:
        """Permanently delete email."""
        try:
            self.service.users().messages().delete(userId="me", id=message_id).execute()
            return True
        except Exception:
            return False

    def _parse_message(self, msg: dict) -> Optional[Email]:
        """Parse Gmail API message into Email model."""
        try:
            headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}

            # Parse sender
            sender_raw = headers.get("from", "")
            sender_name, sender_email = parseaddr(sender_raw)

            # Parse recipients
            to_raw = headers.get("to", "")
            recipients = [parseaddr(r)[1] for r in to_raw.split(",") if r.strip()]

            cc_raw = headers.get("cc", "")
            cc = [parseaddr(r)[1] for r in cc_raw.split(",") if r.strip()]

            # Parse date
            date_str = headers.get("date", "")
            try:
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            # Extract body
            body_text, body_html = self._extract_body(msg["payload"])

            # Extract attachments
            attachments = self._extract_attachments(msg["payload"])

            # Check labels
            labels = msg.get("labelIds", [])

            return Email(
                id=msg["id"],
                thread_id=msg["threadId"],
                subject=headers.get("subject", ""),
                sender=sender_name or sender_email,
                sender_email=sender_email,
                recipients=recipients,
                cc=cc,
                date=date,
                snippet=msg.get("snippet", ""),
                body_text=body_text,
                body_html=body_html,
                labels=labels,
                attachments=attachments,
                is_unread="UNREAD" in labels,
                is_starred="STARRED" in labels,
            )
        except Exception:
            return None

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        """Extract text and HTML body from message payload."""
        body_text = ""
        body_html = ""

        if "body" in payload and payload["body"].get("data"):
            data = payload["body"]["data"]
            decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            mime_type = payload.get("mimeType", "")
            if "html" in mime_type:
                body_html = decoded
            else:
                body_text = decoded

        if "parts" in payload:
            for part in payload["parts"]:
                part_text, part_html = self._extract_body(part)
                if part_text:
                    body_text = part_text
                if part_html:
                    body_html = part_html

        return body_text, body_html

    def _extract_attachments(self, payload: dict) -> list[Attachment]:
        """Extract attachment metadata from message payload."""
        attachments = []

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    attachments.append(
                        Attachment(
                            id=part["body"].get("attachmentId", ""),
                            filename=part["filename"],
                            mime_type=part.get("mimeType", "application/octet-stream"),
                            size=part["body"].get("size", 0),
                        )
                    )
                # Recurse for nested parts
                attachments.extend(self._extract_attachments(part))

        return attachments

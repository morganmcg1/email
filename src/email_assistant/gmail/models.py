"""Data models for Gmail emails."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Email priority levels."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Attachment(BaseModel):
    """Email attachment metadata."""

    id: str
    filename: str
    mime_type: str
    size: int


class Email(BaseModel):
    """Represents a Gmail email message."""

    id: str
    thread_id: str
    subject: str = ""
    sender: str = ""
    sender_email: str = ""
    recipients: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    date: datetime
    snippet: str = ""
    body_text: str = ""
    body_html: str = ""
    labels: list[str] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    is_unread: bool = False
    is_starred: bool = False

    # Triage fields (populated by scorer)
    priority: Optional[Priority] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    needs_reply: Optional[bool] = None


class EmailThread(BaseModel):
    """Represents a Gmail thread with multiple messages."""

    id: str
    subject: str = ""
    messages: list[Email] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    snippet: str = ""

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def participants(self) -> list[str]:
        participants = set()
        for msg in self.messages:
            participants.add(msg.sender_email)
            participants.update(msg.recipients)
        return list(participants)


class Label(BaseModel):
    """Gmail label."""

    id: str
    name: str
    type: str = "user"  # "system" or "user"

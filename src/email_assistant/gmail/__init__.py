"""Gmail API integration."""

from .auth import GmailAuth
from .client import GmailClient
from .models import Email, EmailThread, Attachment

__all__ = ["GmailAuth", "GmailClient", "Email", "EmailThread", "Attachment"]

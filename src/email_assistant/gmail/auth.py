"""Gmail OAuth2 authentication."""

import json
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.labels",
]

DEFAULT_CONFIG_DIR = Path.home() / ".email-assistant"


class GmailAuth:
    """Handles Gmail OAuth2 authentication flow."""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_path = self.config_dir / "credentials.json"
        self.token_path = self.config_dir / "token.json"

    def get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials, refreshing or re-authenticating if needed."""
        creds = self._load_token()

        if creds and creds.valid:
            return creds

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                return creds
            except Exception:
                pass

        return None

    def authenticate(self) -> Credentials:
        """Run OAuth2 flow to get new credentials."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"OAuth credentials file not found at {self.credentials_path}. "
                "Download it from Google Cloud Console and place it there."
            )

        flow = InstalledAppFlow.from_client_secrets_file(str(self.credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        self._save_token(creds)
        return creds

    def is_authenticated(self) -> bool:
        """Check if valid credentials exist."""
        creds = self.get_credentials()
        return creds is not None and creds.valid

    def _load_token(self) -> Optional[Credentials]:
        """Load saved token from disk."""
        if not self.token_path.exists():
            return None

        try:
            return Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
        except Exception:
            return None

    def _save_token(self, creds: Credentials) -> None:
        """Save token to disk."""
        token_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }
        self.token_path.write_text(json.dumps(token_data))

    def revoke(self) -> None:
        """Revoke and delete stored credentials."""
        if self.token_path.exists():
            self.token_path.unlink()

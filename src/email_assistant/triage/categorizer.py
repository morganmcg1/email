"""Email categorization."""

from enum import Enum

from ..gmail.models import Email


class EmailCategory(str, Enum):
    """Email categories."""

    WORK = "work"
    PERSONAL = "personal"
    NEWSLETTER = "newsletter"
    PROMOTIONAL = "promotional"
    SOCIAL = "social"
    TRANSACTIONAL = "transactional"
    SUPPORT = "support"
    OTHER = "other"


class EmailCategorizer:
    """Categorizes emails based on content and sender patterns."""

    # Common patterns for categorization
    NEWSLETTER_PATTERNS = [
        "unsubscribe",
        "newsletter",
        "digest",
        "weekly update",
        "monthly update",
    ]

    PROMOTIONAL_PATTERNS = [
        "sale",
        "discount",
        "offer",
        "deal",
        "promo",
        "limited time",
        "free shipping",
    ]

    SOCIAL_PATTERNS = [
        "linkedin",
        "twitter",
        "facebook",
        "instagram",
        "notification",
        "mentioned you",
        "tagged you",
    ]

    TRANSACTIONAL_PATTERNS = [
        "receipt",
        "invoice",
        "order confirmation",
        "shipping",
        "delivery",
        "payment",
    ]

    def categorize(self, email: Email) -> EmailCategory:
        """Categorize a single email."""
        text = f"{email.subject} {email.snippet} {email.sender}".lower()

        # Check patterns in order of specificity
        if self._matches_patterns(text, self.TRANSACTIONAL_PATTERNS):
            return EmailCategory.TRANSACTIONAL

        if self._matches_patterns(text, self.NEWSLETTER_PATTERNS):
            return EmailCategory.NEWSLETTER

        if self._matches_patterns(text, self.PROMOTIONAL_PATTERNS):
            return EmailCategory.PROMOTIONAL

        if self._matches_patterns(text, self.SOCIAL_PATTERNS):
            return EmailCategory.SOCIAL

        # Default categorization based on labels
        labels_lower = [l.lower() for l in email.labels]

        if "category_social" in labels_lower:
            return EmailCategory.SOCIAL
        if "category_promotions" in labels_lower:
            return EmailCategory.PROMOTIONAL
        if "category_updates" in labels_lower:
            return EmailCategory.NEWSLETTER

        return EmailCategory.OTHER

    def _matches_patterns(self, text: str, patterns: list[str]) -> bool:
        """Check if text matches any of the patterns."""
        return any(pattern in text for pattern in patterns)

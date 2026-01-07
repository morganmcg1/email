"""Email priority scoring using user-defined criteria."""

from ..gmail.models import Email, Priority
from ..storage.db import PrioritizationCriteria


class PriorityScorer:
    """Scores emails based on user-defined prioritization criteria."""

    def __init__(self, criteria: PrioritizationCriteria):
        self.criteria = criteria

    def score(self, email: Email) -> Priority:
        """Score a single email and return its priority level."""
        # Check VIP senders (always high priority)
        if email.sender_email in self.criteria.vip_senders:
            return Priority.HIGH

        # Check VIP domains
        sender_domain = self._get_domain(email.sender_email)
        if sender_domain in self.criteria.vip_domains:
            return Priority.HIGH

        # Check high priority keywords in subject and snippet
        text = f"{email.subject} {email.snippet}".lower()
        for keyword in self.criteria.high_priority_keywords:
            if keyword.lower() in text:
                return Priority.HIGH

        # Check for low priority patterns
        for low_type in self.criteria.low_priority_types:
            low_type_lower = low_type.lower()
            if low_type_lower in text or low_type_lower in email.sender.lower():
                return Priority.LOW

        # Default to medium priority
        return Priority.MEDIUM

    def score_batch(self, emails: list[Email]) -> list[tuple[Email, Priority]]:
        """Score multiple emails and return sorted by priority."""
        scored = [(email, self.score(email)) for email in emails]

        # Sort by priority (HIGH first, then MEDIUM, then LOW)
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        scored.sort(key=lambda x: priority_order[x[1]])

        return scored

    def _get_domain(self, email_address: str) -> str:
        """Extract domain from email address."""
        if "@" in email_address:
            return email_address.split("@")[-1].lower()
        return ""

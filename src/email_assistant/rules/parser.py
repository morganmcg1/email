"""Parse natural language rules into structured format."""

import re
from typing import Optional

from .models import (
    ActionType,
    ConditionField,
    ConditionOperator,
    Rule,
    RuleAction,
    RuleCondition,
)

# Common patterns for parsing natural language rules
TIME_PATTERNS = {
    r"(\d+)\s*days?\s*old": ("older_than", "days"),
    r"(\d+)\s*weeks?\s*old": ("older_than", "weeks"),
    r"(\d+)\s*hours?\s*old": ("older_than", "hours"),
    r"older\s*than\s*(\d+)\s*days?": ("older_than", "days"),
    r"older\s*than\s*(\d+)\s*weeks?": ("older_than", "weeks"),
}

CATEGORY_KEYWORDS = {
    "newsletter": "newsletter",
    "newsletters": "newsletter",
    "promotional": "promotional",
    "promo": "promotional",
    "promotions": "promotional",
    "social": "social",
    "updates": "newsletter",
}

ACTION_KEYWORDS = {
    "archive": ActionType.ARCHIVE,
    "trash": ActionType.TRASH,
    "delete": ActionType.DELETE,
    "mark as read": ActionType.MARK_READ,
    "mark read": ActionType.MARK_READ,
    "star": ActionType.STAR,
    "label": ActionType.ADD_LABEL,
}


class RuleParser:
    """Parses natural language rules into structured Rule objects."""

    def parse(self, text: str) -> Optional[Rule]:
        """Parse natural language rule into structured Rule."""
        text_lower = text.lower().strip()

        conditions = []
        actions = []

        # Try to identify the action
        action = self._parse_action(text_lower)
        if action:
            actions.append(action)

        # Try to parse conditions
        # Category conditions
        for keyword, category in CATEGORY_KEYWORDS.items():
            if keyword in text_lower:
                conditions.append(
                    RuleCondition(
                        field=ConditionField.CATEGORY,
                        operator=ConditionOperator.EQUALS,
                        value=category,
                    )
                )
                break

        # Time-based conditions
        time_condition = self._parse_time_condition(text_lower)
        if time_condition:
            conditions.append(time_condition)

        # Sender conditions
        sender_condition = self._parse_sender_condition(text_lower)
        if sender_condition:
            conditions.append(sender_condition)

        if not actions:
            return None

        return Rule(
            name=self._generate_name(text),
            description=text,
            natural_language=text,
            conditions=conditions,
            actions=actions,
        )

    def _parse_action(self, text: str) -> Optional[RuleAction]:
        """Parse action from text."""
        for keyword, action_type in ACTION_KEYWORDS.items():
            if keyword in text:
                params = {}

                # Handle label action
                if action_type == ActionType.ADD_LABEL:
                    label_match = re.search(r'label\s+["\']?(\w+)["\']?', text)
                    if label_match:
                        params["label"] = label_match.group(1)

                return RuleAction(action_type=action_type, params=params)
        return None

    def _parse_time_condition(self, text: str) -> Optional[RuleCondition]:
        """Parse time-based condition from text."""
        for pattern, (op, unit) in TIME_PATTERNS.items():
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1))
                return RuleCondition(
                    field=ConditionField.DATE,
                    operator=ConditionOperator.OLDER_THAN,
                    value={"amount": value, "unit": unit},
                )
        return None

    def _parse_sender_condition(self, text: str) -> Optional[RuleCondition]:
        """Parse sender-based condition from text."""
        # Match "from user@domain.com" or "from @domain.com"
        email_match = re.search(r"from\s+([^\s]+@[^\s]+)", text)
        if email_match:
            email = email_match.group(1)
            if email.startswith("@"):
                return RuleCondition(
                    field=ConditionField.SENDER_DOMAIN,
                    operator=ConditionOperator.EQUALS,
                    value=email[1:],
                )
            return RuleCondition(
                field=ConditionField.SENDER,
                operator=ConditionOperator.EQUALS,
                value=email,
            )
        return None

    def _generate_name(self, text: str) -> str:
        """Generate a short name from the rule text."""
        # Take first 50 chars, capitalize
        name = text[:50].strip()
        if len(text) > 50:
            name += "..."
        return name.capitalize()

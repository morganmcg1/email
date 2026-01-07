"""Rule execution engine."""

import re
from datetime import datetime, timedelta
from typing import Callable

from ..gmail import GmailClient
from ..gmail.models import Email
from .models import (
    ActionType,
    ConditionField,
    ConditionOperator,
    Rule,
    RuleAction,
    RuleCondition,
)


class RuleEngine:
    """Executes automation rules against emails."""

    def __init__(self, gmail_client: GmailClient):
        self.gmail = gmail_client

    def execute_rule(
        self, rule: Rule, emails: list[Email], dry_run: bool = False
    ) -> list[dict]:
        """Execute a rule against a list of emails."""
        results = []

        for email in emails:
            if self._matches(email, rule):
                actions_taken = []
                for action in rule.actions:
                    if dry_run:
                        actions_taken.append(
                            {"action": action.action_type.value, "would_execute": True}
                        )
                    else:
                        success = self._execute_action(email, action)
                        actions_taken.append(
                            {"action": action.action_type.value, "success": success}
                        )

                results.append(
                    {
                        "email_id": email.id,
                        "subject": email.subject,
                        "matched": True,
                        "actions": actions_taken,
                    }
                )

        return results

    def execute_rules(
        self, rules: list[Rule], emails: list[Email], dry_run: bool = False
    ) -> dict:
        """Execute multiple rules against emails."""
        all_results = {}

        for rule in rules:
            if not rule.enabled:
                continue

            results = self.execute_rule(rule, emails, dry_run)
            if results:
                all_results[rule.name] = results

        return all_results

    def _matches(self, email: Email, rule: Rule) -> bool:
        """Check if email matches rule conditions."""
        if not rule.conditions:
            return True

        results = [self._check_condition(email, cond) for cond in rule.conditions]

        if rule.match_all:
            return all(results)
        return any(results)

    def _check_condition(self, email: Email, condition: RuleCondition) -> bool:
        """Check a single condition against an email."""
        value = self._get_field_value(email, condition.field)
        result = self._evaluate_operator(value, condition.operator, condition.value)

        if condition.negate:
            return not result
        return result

    def _get_field_value(self, email: Email, field: ConditionField):
        """Get the value of a field from an email."""
        field_map: dict[ConditionField, Callable[[], any]] = {
            ConditionField.SENDER: lambda: email.sender_email,
            ConditionField.SENDER_DOMAIN: lambda: (
                email.sender_email.split("@")[-1] if "@" in email.sender_email else ""
            ),
            ConditionField.RECIPIENT: lambda: email.recipients,
            ConditionField.SUBJECT: lambda: email.subject,
            ConditionField.BODY: lambda: email.body_text or email.snippet,
            ConditionField.LABELS: lambda: email.labels,
            ConditionField.DATE: lambda: email.date,
            ConditionField.HAS_ATTACHMENT: lambda: len(email.attachments) > 0,
            ConditionField.IS_UNREAD: lambda: email.is_unread,
            ConditionField.CATEGORY: lambda: email.category,
            ConditionField.PRIORITY: lambda: email.priority,
        }

        getter = field_map.get(field)
        return getter() if getter else None

    def _evaluate_operator(
        self, field_value, operator: ConditionOperator, condition_value
    ) -> bool:
        """Evaluate an operator against a value."""
        if field_value is None:
            return False

        if operator == ConditionOperator.EQUALS:
            if isinstance(field_value, str):
                return field_value.lower() == str(condition_value).lower()
            return field_value == condition_value

        if operator == ConditionOperator.CONTAINS:
            if isinstance(field_value, list):
                return any(condition_value.lower() in str(v).lower() for v in field_value)
            return condition_value.lower() in str(field_value).lower()

        if operator == ConditionOperator.STARTS_WITH:
            return str(field_value).lower().startswith(str(condition_value).lower())

        if operator == ConditionOperator.ENDS_WITH:
            return str(field_value).lower().endswith(str(condition_value).lower())

        if operator == ConditionOperator.MATCHES_REGEX:
            return bool(re.search(condition_value, str(field_value), re.IGNORECASE))

        if operator == ConditionOperator.OLDER_THAN:
            if not isinstance(field_value, datetime):
                return False
            delta = self._parse_time_delta(condition_value)
            threshold = datetime.now() - delta
            return field_value < threshold

        if operator == ConditionOperator.NEWER_THAN:
            if not isinstance(field_value, datetime):
                return False
            delta = self._parse_time_delta(condition_value)
            threshold = datetime.now() - delta
            return field_value > threshold

        if operator == ConditionOperator.IN_LIST:
            if isinstance(condition_value, list):
                return field_value in condition_value
            return False

        return False

    def _parse_time_delta(self, value: dict) -> timedelta:
        """Parse time delta from condition value."""
        amount = value.get("amount", 0)
        unit = value.get("unit", "days")

        if unit in ("day", "days"):
            return timedelta(days=amount)
        if unit in ("week", "weeks"):
            return timedelta(weeks=amount)
        if unit in ("hour", "hours"):
            return timedelta(hours=amount)
        if unit in ("minute", "minutes"):
            return timedelta(minutes=amount)

        return timedelta(days=amount)

    def _execute_action(self, email: Email, action: RuleAction) -> bool:
        """Execute a single action on an email."""
        action_map: dict[ActionType, Callable[[], bool]] = {
            ActionType.ARCHIVE: lambda: self.gmail.archive_email(email.id),
            ActionType.TRASH: lambda: self.gmail.trash_email(email.id),
            ActionType.DELETE: lambda: self.gmail.delete_email(email.id),
            ActionType.MARK_READ: lambda: self.gmail.mark_read(email.id),
            ActionType.MARK_UNREAD: lambda: self.gmail.mark_unread(email.id),
            ActionType.STAR: lambda: self.gmail.star_email(email.id),
            ActionType.UNSTAR: lambda: self.gmail.unstar_email(email.id),
            ActionType.ADD_LABEL: lambda: self.gmail.modify_labels(
                email.id, add_labels=[action.params.get("label", "")]
            ),
            ActionType.REMOVE_LABEL: lambda: self.gmail.modify_labels(
                email.id, remove_labels=[action.params.get("label", "")]
            ),
        }

        executor = action_map.get(action.action_type)
        if executor:
            return executor()
        return False

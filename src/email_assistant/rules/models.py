"""Data models for automation rules."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ConditionOperator(str, Enum):
    """Operators for rule conditions."""

    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    MATCHES_REGEX = "matches_regex"
    OLDER_THAN = "older_than"
    NEWER_THAN = "newer_than"
    IN_LIST = "in_list"


class ConditionField(str, Enum):
    """Fields that can be used in conditions."""

    SENDER = "sender"
    SENDER_DOMAIN = "sender_domain"
    RECIPIENT = "recipient"
    SUBJECT = "subject"
    BODY = "body"
    LABELS = "labels"
    DATE = "date"
    HAS_ATTACHMENT = "has_attachment"
    IS_UNREAD = "is_unread"
    CATEGORY = "category"
    PRIORITY = "priority"


class ActionType(str, Enum):
    """Types of actions rules can take."""

    ARCHIVE = "archive"
    TRASH = "trash"
    DELETE = "delete"
    ADD_LABEL = "add_label"
    REMOVE_LABEL = "remove_label"
    MARK_READ = "mark_read"
    MARK_UNREAD = "mark_unread"
    STAR = "star"
    UNSTAR = "unstar"
    FORWARD = "forward"


class RuleCondition(BaseModel):
    """A single condition in a rule."""

    field: ConditionField
    operator: ConditionOperator
    value: Any
    negate: bool = False


class RuleAction(BaseModel):
    """An action to take when rule matches."""

    action_type: ActionType
    params: dict[str, Any] = Field(default_factory=dict)


class Rule(BaseModel):
    """An automation rule."""

    id: Optional[int] = None
    name: str
    description: str = ""
    natural_language: Optional[str] = None
    conditions: list[RuleCondition] = Field(default_factory=list)
    actions: list[RuleAction] = Field(default_factory=list)
    match_all: bool = True  # True = AND all conditions, False = OR
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "description": self.description,
            "natural_language": self.natural_language,
            "conditions": [c.model_dump() for c in self.conditions],
            "actions": [a.model_dump() for a in self.actions],
            "match_all": self.match_all,
            "enabled": self.enabled,
        }

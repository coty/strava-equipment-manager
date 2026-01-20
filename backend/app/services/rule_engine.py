import re
from typing import Any
from app.models.activity import Activity
from app.models.rule import Rule, RuleCondition


class RuleEngine:
    """Engine for evaluating rules against activities."""

    # Equipment map for lookups (set before evaluation)
    _equipment_map: dict[int, str] = {}

    @classmethod
    def set_equipment_map(cls, equipment_map: dict[int, str]):
        """Set the equipment ID to name mapping for lookups."""
        cls._equipment_map = equipment_map

    @classmethod
    def evaluate_condition(cls, activity: Activity, condition: RuleCondition) -> bool:
        """Evaluate a single condition against an activity."""
        # Handle virtual fields that need lookups
        if condition.field == "current_gear_name":
            # Look up equipment name from gear_id
            if activity.gear_id and activity.gear_id in cls._equipment_map:
                field_value = cls._equipment_map[activity.gear_id]
            else:
                field_value = None
        else:
            # Get the field value from the activity
            field_value = getattr(activity, condition.field, None)

        if field_value is None:
            return False

        # Convert to string for comparison (except for booleans and numbers)
        condition_value = condition.value

        # Handle different operators
        operator = condition.operator.lower()

        if operator == "equals":
            if isinstance(field_value, bool):
                return field_value == (condition_value.lower() == "true")
            return str(field_value).lower() == str(condition_value).lower()

        elif operator == "not_equals":
            if isinstance(field_value, bool):
                return field_value != (condition_value.lower() == "true")
            return str(field_value).lower() != str(condition_value).lower()

        elif operator == "contains":
            return str(condition_value).lower() in str(field_value).lower()

        elif operator == "not_contains":
            return str(condition_value).lower() not in str(field_value).lower()

        elif operator == "starts_with":
            return str(field_value).lower().startswith(str(condition_value).lower())

        elif operator == "ends_with":
            return str(field_value).lower().endswith(str(condition_value).lower())

        elif operator == "regex":
            try:
                pattern = re.compile(condition_value, re.IGNORECASE)
                return bool(pattern.search(str(field_value)))
            except re.error:
                return False

        elif operator == "greater_than":
            try:
                return float(field_value) > float(condition_value)
            except (ValueError, TypeError):
                return False

        elif operator == "less_than":
            try:
                return float(field_value) < float(condition_value)
            except (ValueError, TypeError):
                return False

        elif operator == "greater_than_or_equal":
            try:
                return float(field_value) >= float(condition_value)
            except (ValueError, TypeError):
                return False

        elif operator == "less_than_or_equal":
            try:
                return float(field_value) <= float(condition_value)
            except (ValueError, TypeError):
                return False

        return False

    @classmethod
    def evaluate_rule(cls, activity: Activity, rule: Rule) -> bool:
        """
        Evaluate all conditions in a rule against an activity.
        Returns True if the activity matches all conditions.
        """
        if not rule.conditions:
            return False

        # Group conditions by logic (AND/OR)
        # For simplicity, we'll evaluate all conditions with AND logic first
        # OR logic would require more complex grouping

        results = []
        current_logic = "AND"

        for condition in rule.conditions:
            result = cls.evaluate_condition(activity, condition)
            results.append((result, condition.logic))

        # Evaluate with AND/OR logic
        # Start with the first result
        if not results:
            return False

        final_result = results[0][0]

        for i in range(1, len(results)):
            result, logic = results[i]
            prev_logic = results[i - 1][1]

            if prev_logic.upper() == "AND":
                final_result = final_result and result
            else:  # OR
                final_result = final_result or result

        return final_result

    @classmethod
    def find_matching_activities(
        cls, activities: list[Activity], rule: Rule
    ) -> list[Activity]:
        """Find all activities that match a rule."""
        return [
            activity
            for activity in activities
            if cls.evaluate_rule(activity, rule)
        ]

    @classmethod
    def find_first_matching_rule(
        cls, activity: Activity, rules: list[Rule]
    ) -> Rule | None:
        """
        Find the first rule that matches an activity.
        Rules should be sorted by priority.
        """
        for rule in sorted(rules, key=lambda r: r.priority):
            if rule.is_active and cls.evaluate_rule(activity, rule):
                return rule
        return None

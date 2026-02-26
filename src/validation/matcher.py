import re
from typing import Any, Union

from src.validation.rules import ValidationRule


class Matcher:
    """
    Applies a given ValidationRule to a target value.
    """

    def match(self, rule: ValidationRule, target_value: Any) -> bool:
        if rule.type == "present":
            return target_value is not None
        
        if target_value is None:
            return False

        # Convert target_value to string for consistent comparison, especially for regex/contains
        target_str = str(target_value)
        expected_str = str(rule.value) if rule.value is not None else ""

        if not rule.case_sensitive:
            target_str = target_str.lower()
            expected_str = expected_str.lower()

        if rule.type == "exact":
            return target_str == expected_str
        elif rule.type == "regex":
            return re.search(expected_str, target_str) is not None
        elif rule.type == "contains":
            return expected_str in target_str
        else:
            raise ValueError(f"Unknown validation rule type: {rule.type}")


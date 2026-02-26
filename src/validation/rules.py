from typing import Dict, Literal, Union

from pydantic import BaseModel, Field


class ValidationRule(BaseModel):
    """Base model for all validation rules."""
    type: Literal["exact", "regex", "contains", "present"] = Field(
        ..., description="The type of validation to perform."
    )
    value: Union[str, int, float, bool, None] = Field(
        None,
        description="The expected value for comparison. Not used for 'present' type.",
    )
    case_sensitive: bool = Field(
        True, description="Whether the comparison should be case-sensitive."
    )


class ExpectedTag(BaseModel):
    """
    Represents an expected tag with its validation rules.
    If 'rules' is not provided, it defaults to an 'exact' match rule with the 'value'
    from the parent dictionary.
    """

    key: str = Field(..., description="The key of the expected tag parameter.")
    value: Union[str, int, float, bool, None] = Field(
        None, description="The expected value for the tag parameter."
    )
    rules: Dict[str, ValidationRule] = Field(
        default_factory=dict,
        description="Dictionary of validation rules for this tag. Key is rule name.",
    )

    # Allow direct initialization with a value, which implies an "exact" rule
    def __init__(self, **data):
        super().__init__(**data)
        if not self.rules and self.value is not None:
            self.rules["default"] = ValidationRule(type="exact", value=self.value)


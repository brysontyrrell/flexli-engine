from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    StrictFloat,
    StrictStr,
    field_validator,
)


def attr_is_expression(v: str):
    if not v.startswith("::"):
        raise ValueError("Attribute must be JMESPath expression")
    return v


def value_is_expression(v):
    if isinstance(v, str) and not v.startswith("::"):
        raise ValueError("String value MUST be JMESPath expression")
    return v


class StringOperators(str, Enum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"
    starts_with = "starts_with"


class StringAttribute(BaseModel):
    type: Literal["String"]
    attribute: str
    operator: StringOperators
    value: StrictStr

    _attr_is_expression = field_validator("attribute")(attr_is_expression)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class NumberOperators(str, Enum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"


class NumberAttribute(BaseModel):
    type: Literal["Number"]
    attribute: str
    operator: NumberOperators
    value: Union[StrictInt, StrictFloat, str] = Field(union_mode="left_to_right")

    _attr_is_expression = field_validator("attribute")(attr_is_expression)
    _value_is_expression = field_validator("value")(value_is_expression)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class BooleanOperators(str, Enum):
    EQ = "eq"
    NE = "ne"


class BooleanAttribute(BaseModel):
    type: Literal["Boolean"]
    attribute: str
    operator: BooleanOperators
    value: Union[StrictBool, str] = Field(union_mode="left_to_right")

    _attr_is_expression = field_validator("attribute")(attr_is_expression)
    _value_is_expression = field_validator("value")(value_is_expression)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DateOperators(str, Enum):
    BEFORE = "before"
    AFTER = "after"


class DateAttribute(BaseModel):
    type: Literal["Date"]
    attribute: str
    operator: DateOperators
    value: Union[date, datetime, str] = Field(union_mode="left_to_right")

    _attr_is_expression = field_validator("attribute", mode="after")(attr_is_expression)
    _value_is_expression = field_validator("value", mode="after")(value_is_expression)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class VersionOperators(str, Enum):
    EQ = "eq"
    NE = "ne"
    LT = "lt"
    LTE = "lte"
    GT = "gt"
    GTE = "gte"


class VersionAttribute(BaseModel):
    type: Literal["Version"]
    attribute: str
    operator: VersionOperators
    value: str  # TODO: make this a version (packaging)

    _attr_is_expression = field_validator("attribute")(attr_is_expression)
    _value_is_expression = field_validator("value")(value_is_expression)

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


CriteriaAttributes = Annotated[
    Union[
        StringAttribute,
        NumberAttribute,
        BooleanAttribute,
        DateAttribute,
        VersionAttribute,
    ],
    Field(discriminator="type"),
]


class CriteriaOperators(str, Enum):
    AND = "and"
    OR = "or"


class Criteria(BaseModel):
    operator: CriteriaOperators = CriteriaOperators.AND
    attributes: list[CriteriaAttributes] = Field(min_length=1, max_length=10)

    model_config = ConfigDict(use_enum_values=True)


class OnFailOptions(str, Enum):
    SKIP = "skip"
    STOP = "stop"
    FAIL = "fail"


class Condition(BaseModel):
    operator: CriteriaOperators = CriteriaOperators.AND
    criteria: list[Criteria] = Field(min_length=1, max_length=10)
    on_fail: OnFailOptions = OnFailOptions.FAIL

    model_config = ConfigDict(extra="forbid", use_enum_values=True)

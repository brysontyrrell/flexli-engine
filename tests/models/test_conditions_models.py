from datetime import datetime

from pydantic import TypeAdapter, ValidationError
import pytest

from src.layers.layer.conditions.models import (
    Condition,
    CriteriaAttributes,
    DateAttribute,
)

CriteriaAttributesAdapter = TypeAdapter(CriteriaAttributes)


def test_condition_no_criteria():
    data = {"criteria": []}
    with pytest.raises(ValidationError) as err:
        Condition.model_validate(data)

    errors = err.value.errors()
    assert (
        errors[0]["msg"] == "List should have at least 1 item after validation, not 0"
    )


def test_condition_too_many_criteria():
    # Max 10 criteria in a condition
    data = {"criteria": [{} for _ in range(11)]}
    with pytest.raises(ValidationError) as err:
        Condition.model_validate(data)

    errors = err.value.errors()
    assert (
        errors[0]["msg"] == "List should have at most 10 items after validation, not 11"
    )


def test_criteria_too_many_attributes():
    # Max 10 attributes in a criteria
    data = {"criteria": [{"attributes": [{} for _ in range(11)]}]}
    with pytest.raises(ValidationError) as err:
        Condition.model_validate(data)

    errors = err.value.errors()
    assert (
        errors[0]["msg"] == "List should have at most 10 items after validation, not 11"
    )


def test_condition_defaults():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "String",
                        "attribute": "::foo",
                        "operator": "eq",
                        "value": "bar",
                    }
                ]
            }
        ]
    }
    cond1 = Condition.model_validate(data)
    assert cond1.on_fail == "fail"
    assert cond1.operator == "and"
    assert cond1.criteria[0].operator == "and"
    assert cond1.criteria[0].attributes[0].type == "String"


def test_condition_or_operators():
    data = {
        "on_fail": "stop",
        "operator": "or",
        "criteria": [
            {
                "operator": "or",
                "attributes": [
                    {
                        "type": "String",
                        "attribute": "::foo",
                        "operator": "eq",
                        "value": "bar",
                    }
                ],
            }
        ],
    }
    cond1 = Condition.model_validate(data)
    assert cond1.on_fail == "stop"
    assert cond1.operator == "or"
    assert cond1.criteria[0].operator == "or"


def test_condition_on_fail_skip():
    data = {
        "on_fail": "skip",
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "String",
                        "attribute": "::foo",
                        "operator": "eq",
                        "value": "bar",
                    }
                ],
            }
        ],
    }
    cond1 = Condition.model_validate(data)
    assert cond1.on_fail == "skip"


def test_number_type_float():
    data = {
        "type": "Number",
        "attribute": "::foo",
        "operator": "lt",
        "value": 1.1,
    }
    attr1 = CriteriaAttributesAdapter.validate_python(data)
    assert attr1.type == "Number"


def test_number_type_int():
    data = {
        "type": "Number",
        "attribute": "::foo",
        "operator": "gt",
        "value": 1,
    }
    attr1 = CriteriaAttributesAdapter.validate_python(data)
    assert attr1.type == "Number"


def test_boolean_type():
    data = {
        "type": "Boolean",
        "attribute": "::foo",
        "operator": "ne",
        "value": True,
    }
    attr1 = CriteriaAttributesAdapter.validate_python(data)
    assert attr1.type == "Boolean"


def test_date_type():
    data = {
        "type": "Date",
        "attribute": "::foo",
        "operator": "before",
        "value": "2023-11-24T12:00:00Z",
    }
    attr1 = CriteriaAttributesAdapter.validate_python(data)
    assert attr1.type == "Date"
    assert isinstance(attr1.value, datetime)


def test_version_type():
    pass


def test_multiple_criteria_1():
    data = {
        "criteria": [
            {
                "attributes": [
                    {
                        "type": "String",
                        "attribute": "::foo",
                        "operator": "eq",
                        "value": "bar",
                    },
                    {
                        "type": "String",
                        "attribute": "::bar",
                        "operator": "ne",
                        "value": "baz",
                    },
                ],
            },
            {
                "operator": "or",
                "attributes": [
                    {
                        "type": "Number",
                        "attribute": "::a",
                        "operator": "gte",
                        "value": 5,
                    },
                    {
                        "type": "Number",
                        "attribute": "::b",
                        "operator": "lt",
                        "value": 10,
                    },
                ],
            },
        ],
    }
    cond1 = Condition.model_validate(data)
    assert cond1.criteria[0].operator == "and"
    assert cond1.criteria[1].operator == "or"
    assert len(cond1.criteria[0].attributes) == 2
    assert len(cond1.criteria[1].attributes) == 2

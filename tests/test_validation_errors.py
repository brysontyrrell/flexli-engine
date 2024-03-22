from jsonschema import Draft202012Validator, FormatChecker

from src.layers.layer.apis.models import json_schema_validation


def test_json_error_skip_expressions():
    body = {"foo": "::path", "bar": {}}
    validator = Draft202012Validator(
        {
            "properties": {"foo": {"type": "array"}, "bar": {"type": "object"}},
            "required": ["foo", "bar"],
        },
        format_checker=FormatChecker(),
    )

    errors = json_schema_validation(data=body, validator=validator)
    assert not errors

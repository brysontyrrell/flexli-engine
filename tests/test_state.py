import jmespath

from transforms import (
    can_format_string,
    dict_from_key_path,
    find_value,
    find_values_dict,
    flexli_options,
    key_path_from_string,
    return_value,
)


def test_find_value():
    data = {"a": {"b": {"c": 1}, "d.e": 2}}
    assert find_value(["a", "b"], data) == {"c": 1}
    assert find_value(["a", "b", "c"], data) == 1
    assert find_value(["a", "d.e"], data) == 2


def test_key_path():
    assert key_path_from_string("a.b.c") == ["a", "b", "c"]
    assert key_path_from_string("a.'d.e'") == ["a", "d.e"]
    assert key_path_from_string('''a.b.'c.d'.e."f"''') == ["a", "b", "c.d", "e", "f"]


def test_return_value():
    data = {"a": {"b": {"c": 1}, "d": [2, 3, 4]}}
    assert return_value("::a.b.c", data) == 1
    assert return_value("::a.d", data) == [2, 3, 4]
    assert return_value("::a.d[1]", data) == 3
    assert return_value("value", data) == "value"


def test_dict_from_key_path():
    assert dict_from_key_path(["a"], {"b": None}) == {"a": {"b": None}}
    assert dict_from_key_path(["a", "b"], {"c": 1}) == {"a": {"b": {"c": 1}}}


def test_can_format_string():
    assert can_format_string("My value is 1", format_vars=["a"]) is False
    assert can_format_string("My value is {a}", format_vars=["a"]) is True
    assert can_format_string("My value is {a}", format_vars=[]) is False
    assert can_format_string("My value is {a}", format_vars=["b"]) is False
    assert can_format_string("My value is {a}", format_vars=["a", "b"]) is True


def test_find_values_dict():
    data = {"a": {"b": {"c": 1}, "d": [2, 3, 4]}}
    assert find_values_dict({"a": "::a.b.c"}, data) == {"a": 1}
    assert find_values_dict({"b": "::a.d[1]"}, data) == {"b": 3}


def test_find_and_format_strings():
    pass


def test_flexli_diff_arrays_function():
    result = jmespath.search(
        "flexli_diff_arrays(array_1, array_2)",
        {"array_1": [1, 2, 3, 4], "array_2": [2, 3, 5, 6]},
        options=flexli_options,
    )
    assert result["added"] == [5, 6]
    assert result["removed"] == [1, 4]


# def test_return_value_formatted():
#     data = {"a": {"b": {"c": 1}, "d": [2, 3, 4]}}
#     assert (
#         return_value("my value is {a}", data, find_values_dict({"a": "::a.b.c"}, data))
#         == "my value is 1"
#     )
#     assert (
#         return_value("my value is {b}", data, find_values_dict({"b": "::a.d[1]"}, data))
#         == "my value is 3"
#     )
#     assert (
#         return_value(
#             "my value is {a} and {b}",
#             data,
#             find_values_dict({"a": "::a.b.c", "b": "::a.d[1]"}, data),
#         )
#         == "my value is 1 and 3"
#     )
#
#
# def test_return_value_cannot_format():
#     data = {"a": {"b": {"c": 1}, "d": [2, 3, 4]}}
#     # If any referenced vars are missing the string will not be formatted.
#     assert (
#         return_value(
#             "my value is {a} and {b}", data, find_values_dict({"a": "::a.b.c"}, data)
#         )
#         == "my value is {a} and {b}"
#     )

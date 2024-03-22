import copy
import re
import string
from typing import Union


import jmespath
from jmespath.exceptions import JMESPathError

from .core import flexli_options


key_path_splitter = re.compile(r"""((?:[^\."']|"[^"]*"|'[^']*')+)""")


class TransformError(Exception):
    pass


# Copied from pydantic.v1.utils - function is deprecated in v2
def deep_update(mapping: dict, *updating_mappings: dict) -> dict:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if (
                k in updated_mapping
                and isinstance(updated_mapping[k], dict)
                and isinstance(v, dict)
            ):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def key_path_from_string(path: str) -> list[str]:
    """Convert a string representing a basic key path to a list of strings representing
    the key names.

    Example: "a.b.c" -> ["a", "b", "c"]
    """
    return [i.strip("\"'") for i in key_path_splitter.split(path)[1::2]]


def dict_from_key_path(path: list[str], value) -> dict:
    """Returns a nested dictionary generated from a key path list with the value
    set at the innermost level.

    Example: value: "foo", key path: ["a", "b", "c"] -> {"a": {"b": {"c": "foo}}}
    """
    base = {path[-1]: value}
    for key in reversed(path[:-1]):
        base = {key: base}
    return base


def can_format_string(value: str, format_vars: list[str]) -> bool:
    """Returns 'True' if the value is a string with format fields and those fields are present in
    the 'format_vars' list."""
    parsed_vars = [t[1] for t in string.Formatter().parse(value) if t[1] is not None]
    if parsed_vars and format_vars:
        return all([v in format_vars for v in parsed_vars])
    return False


def return_value(value, source: dict):
    """Takes in a 'value' of any type and a 'source' dictionary that will be searched if the value
    is a JMESPath expression. The original value is returned if it is not an expression. Otherwise,
    the expression's search result is returned.
    """
    try:
        if isinstance(value, str) and value.startswith("::"):
            search_value = value[2:]
            return (
                jmespath.search(search_value, source, options=flexli_options)
                if len(search_value) > 0
                else source
            )
        else:
            return value
    except JMESPathError as err:
        # TODO: Need to raise an exception that can be parsed by the state machine
        raise TransformError(str(err))


def key_path_is_ignored(
    current: str | int, ignored_paths: list[list[str]] | None
) -> bool:
    """Takes a current marker (dictionary key or list index) and compares it to a list of key-paths.
    If the list of key-paths contains any entry with only one value and that value is equal to the
    current value it returns ``True``.
    """
    if not ignored_paths:
        return False

    for key_path in ignored_paths:
        if len(key_path) == 1 and current == key_path[0]:
            return True
    else:
        return False


def check_next_ignored_paths(
    current: str | int, ignored_paths: list[list[str]] | None
) -> list | None:
    """Takes a current marker (dictionary key or list index) and compares it to a list of key-paths.
    The resulting list of new key-paths will include the paths following the current value if there
    was a match at the start of the key-path.
    """
    if not ignored_paths:
        return None

    next_key_paths = []
    for key_path in ignored_paths:
        if len(key_path) > 1 and current == key_path[0]:
            next_key_paths.append(key_path[1:])

    return next_key_paths


def find_and_evaluate_expressions(
    target: dict,
    source: Union[dict, list],
    ignored_paths: list[list[str]] = None,
):
    if isinstance(target, dict):
        for k, v in target.items():
            if key_path_is_ignored(current=k, ignored_paths=ignored_paths):
                continue

            if isinstance(v, str) and v.startswith("::"):
                target[k] = return_value(v, source)
            elif isinstance(v, Union[dict, list]):
                find_and_evaluate_expressions(
                    v, source, ignored_paths=check_next_ignored_paths(k, ignored_paths)
                )

    elif isinstance(target, list):
        for idx, i in enumerate(target):
            if key_path_is_ignored(current=idx, ignored_paths=ignored_paths):
                continue

            if isinstance(i, str) and i.startswith("::"):
                target[idx] = return_value(i, source)
            elif isinstance(i, Union[dict, list]):
                find_and_evaluate_expressions(
                    i,
                    source,
                    ignored_paths=check_next_ignored_paths(idx, ignored_paths),
                )


def find_and_format_strings(
    target: Union[dict, list],
    format_vars: dict,
    ignored_paths: list[list[str]] = None,
):
    """Takes a 'source' dictionary and a dictionary of 'format_vars' that contains variable names
    and their values. The source dictionary is traversed to test string values that contain format
    fields (curly braces with a name: {name}) and then format them if all the string variables are
    present in the format_vars.
    """
    if isinstance(target, dict):
        for k, v in target.items():
            if key_path_is_ignored(current=k, ignored_paths=ignored_paths):
                continue

            if isinstance(v, str) and can_format_string(
                value=v, format_vars=list(format_vars.keys())
            ):
                target[k] = v.format(**format_vars)
            elif isinstance(v, Union[dict, list]):
                find_and_format_strings(
                    v,
                    format_vars,
                    ignored_paths=check_next_ignored_paths(k, ignored_paths),
                )
    elif isinstance(target, list):
        for idx, i in enumerate(target):
            if key_path_is_ignored(current=idx, ignored_paths=ignored_paths):
                continue

            if isinstance(i, str) and can_format_string(
                value=i, format_vars=list(format_vars.keys())
            ):
                target[idx] = i.format(**format_vars)
            elif isinstance(i, Union[dict, list]):
                find_and_format_strings(
                    i,
                    format_vars,
                    ignored_paths=check_next_ignored_paths(idx, ignored_paths),
                )


def find_value(path: list[str], source: dict):
    """Given a key path list, return the value of the innermost key."""
    if len(path) == 1:
        return source[path[0]]
    else:
        return find_value(path[1:], source[path[0]])


def find_values_dict(values_dict: dict[str, str], source: dict) -> dict:
    """Takes in a dictionary of key names and values/JMESPath expressions and returns a new
    dictionary containing the resulting values from the source.
    """
    new_dict = {}
    for k, v in values_dict.items():
        new_dict[k] = return_value(value=v, source=source)

    return new_dict


def transform(
    source: dict,
    target: dict = None,
    updates: dict = None,
    variables: dict[str, str] = None,
    ignored_paths: list[str] = None,
) -> dict:
    """Process JMESPath expressions and formattable strings returning a new object.

    :param source: A dictionary that contains data that will be referenced by JMESPath expressions
        in the ``updates`` and ``variables`` dictionaries.

    :param target: A dictionary that will be modified and returned.

    :param updates: A dictionary of key-path locations and JMESPath expressions that will reference
        the ``source`` dictionary to apply to the ``target`` dictionary.

    :param variables: A dictionary of names and JMESPath expressions. Variables are resolved and
        applied to formattable strings after the ``updates`` are processed.

    :param ignored_paths: A list of key-paths that will be ignored when processing JMESPath
        expressions and string formatting.

    """
    # A copy of the `source` will be returned if the update wildcard is detected
    if updates and ("::", "::") in updates.items():
        return copy.deepcopy(source)

    # The `ignored_paths` are converted to key-path lists
    if ignored_paths:
        ignored_paths = [key_path_from_string(i) for i in ignored_paths]

    # If a target was provided a copy is made
    target_copy = copy.deepcopy(target) if target else {}

    # The `target_copy` has any `updates` applied from the `source`
    if updates:
        target_updates = [
            dict_from_key_path(
                key_path_from_string(k),
                return_value(value=v, source=source),
            )
            for k, v in updates.items()
        ]

        target_copy = deep_update(target_copy, *target_updates)

    # Formattable strings are found and processed
    if variables:
        find_and_format_strings(
            target=target_copy,
            format_vars=find_values_dict(values_dict=variables, source=source),
        )

    # JMESPath expressions are found and processed (this is always done)
    find_and_evaluate_expressions(
        target=target_copy, source=source, ignored_paths=ignored_paths
    )

    return target_copy

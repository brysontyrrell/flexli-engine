import copy

from transforms import (
    check_next_ignored_paths,
    find_and_evaluate_expressions,
    find_and_format_strings,
    key_path_is_ignored,
    transform,
)


def test_key_path_is_ignored():
    assert key_path_is_ignored(current="a", ignored_paths=[["a"]])
    assert key_path_is_ignored(current="a", ignored_paths=[["b"], ["a"]])


def test_key_path_is_not_ignored():
    assert not key_path_is_ignored(current="a", ignored_paths=[["b"]])
    assert not key_path_is_ignored(current="a", ignored_paths=[["b", "a"], ["c"]])


def test_check_next_ignored_paths():
    next_ignored_paths = check_next_ignored_paths(
        current="a",
        ignored_paths=[["a"], ["a", "b"], ["b"]],
    )
    assert next_ignored_paths == [["b"]]


def test_check_next_ignored_paths_are_none():
    next_ignored_paths = check_next_ignored_paths(
        current="c",
        ignored_paths=[["a"], ["a", "b"], ["b"]],
    )
    assert next_ignored_paths == []


def test_find_and_evaluate_no_ignore():
    target = {"a": "::foo", "b": {"c": "::bar[0]"}, "d": ["::baz"]}
    source = {"foo": 1, "bar": [2], "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_evaluate_expressions(target=new_target, source=source)

    assert target["a"] == "::foo"
    assert target["b"]["c"] == "::bar[0]"
    assert target["d"][0] == "::baz"

    assert new_target["a"] == 1
    assert new_target["b"]["c"] == 2
    assert new_target["d"][0] == 3


def test_find_and_evaluate_with_shallow_ignore():
    target = {"a": "::foo", "b": {"c": "::bar[0]"}, "d": ["::baz"]}
    source = {"foo": 1, "bar": [2], "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_evaluate_expressions(
        target=new_target, source=source, ignored_paths=[["b"]]
    )

    assert target["a"] == "::foo"
    assert target["d"][0] == "::baz"

    assert new_target["a"] == 1
    assert new_target["b"]["c"] == "::bar[0]"
    assert new_target["d"][0] == 3


def test_find_and_evaluate_with_nested_ignore():
    target = {"a": "::foo", "b": {"c": "::bar[0]", "e": "::bar[0]"}, "d": ["::baz"]}
    source = {"foo": 1, "bar": [2], "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_evaluate_expressions(
        target=new_target, source=source, ignored_paths=[["b", "c"]]
    )

    assert target["a"] == "::foo"
    assert target["b"]["e"] == "::bar[0]"
    assert target["d"][0] == "::baz"

    assert new_target["a"] == 1
    assert new_target["b"]["c"] == "::bar[0]"
    assert new_target["b"]["e"] == 2
    assert new_target["d"][0] == 3


def test_find_and_evaluate_with_multiple_ignore():
    target = {"a": {"b": "::foo", "c": "::bar[0]", "d": ["::baz"]}, "e": "::bar[0]"}
    source = {"foo": 1, "bar": [2], "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_evaluate_expressions(
        target=new_target,
        source=source,
        ignored_paths=[["a", "b"], ["a", "d", 0], ["e"]],
    )

    assert target["a"]["c"] == "::bar[0]"

    assert new_target["a"]["b"] == "::foo"
    assert new_target["a"]["c"] == 2
    assert new_target["a"]["d"][0] == "::baz"
    assert new_target["e"] == "::bar[0]"


def test_find_and_format_strings_multi():
    target = {"a": "{foo} plus {bar} equals {baz}"}
    format_vars = {"foo": 1, "bar": 2, "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_format_strings(target=new_target, format_vars=format_vars)

    assert new_target["a"] == "1 plus 2 equals 3"


def test_find_and_format_strings_no_ignore():
    target = {"a": "is {foo}", "b": {"c": "is {bar}"}, "d": ["is {baz}"]}
    format_vars = {"foo": 1, "bar": 2, "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_format_strings(target=new_target, format_vars=format_vars)

    assert target["a"] == "is {foo}"
    assert target["b"]["c"] == "is {bar}"
    assert target["d"][0] == "is {baz}"

    assert new_target["a"] == "is 1"
    assert new_target["b"]["c"] == "is 2"
    assert new_target["d"][0] == "is 3"


def test_find_and_format_strings_with_shallow_ignore():
    target = {"a": "is {foo}", "b": {"c": "is {bar}"}, "d": ["is {baz}"]}
    format_vars = {"foo": 1, "bar": 2, "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_format_strings(
        target=new_target, format_vars=format_vars, ignored_paths=[["b"]]
    )
    assert target["a"] == "is {foo}"
    assert target["d"][0] == "is {baz}"

    assert new_target["a"] == "is 1"
    assert new_target["b"]["c"] == "is {bar}"
    assert new_target["d"][0] == "is 3"


def test_find_and_format_strings_with_nested_ignore():
    target = {
        "a": "is {foo}",
        "b": {"c": "is {bar}", "e": "is {bar}"},
        "d": ["is {baz}"],
    }
    format_vars = {"foo": 1, "bar": 2, "baz": 3}

    new_target = copy.deepcopy(target)
    find_and_format_strings(
        target=new_target, format_vars=format_vars, ignored_paths=[["b", "c"]]
    )

    assert target["a"] == "is {foo}"
    assert target["b"]["e"] == "is {bar}"
    assert target["d"][0] == "is {baz}"

    assert new_target["a"] == "is 1"
    assert new_target["b"]["c"] == "is {bar}"
    assert new_target["b"]["e"] == "is 2"
    assert new_target["d"][0] == "is 3"


def test_transform():
    source = {"general": {"id": "12345", "name": "Mac"}}
    target = {"a": "foo", "b": {"c": "bar", "d": "baz"}}
    updates = {"id": "::general.id", "b.e": "foobar", "'f.g'": 1}

    updated_target = transform(target=target, source=source, updates=updates)

    assert "id" not in target
    assert "e" not in target["b"]
    assert "f" not in target

    assert updated_target["a"] == "foo"
    assert updated_target["b"] == {"c": "bar", "d": "baz", "e": "foobar"}
    assert updated_target["id"] == "12345"
    assert updated_target["f.g"] == 1


def test_wildcard_transform():
    source = {"c": 3, "p": 0}
    target = {"foo": "bar", "baz": {"a": 1, "b": 2}}
    updates = {"::": "::"}

    updated_target = transform(target=target, source=source, updates=updates)

    assert target == {"foo": "bar", "baz": {"a": 1, "b": 2}}

    assert updated_target == {"c": 3, "p": 0}


def test_nested_wildcard_transform():
    source = {"c": 3, "p": 0}
    target = {"foo": "bar", "baz": {"a": 1, "b": 2}}
    updates = {"baz": "::", "new": "::"}

    updated_target = transform(target=target, source=source, updates=updates)

    assert target == {"foo": "bar", "baz": {"a": 1, "b": 2}}

    assert updated_target["baz"] == {"a": 1, "b": 2, "c": 3, "p": 0}
    assert updated_target["new"] == {"c": 3, "p": 0}


def test_transform_with_formatting():
    source = {"foo": 1, "bar": 2, "baz": 3}
    target = {"a": "is {foo}", "b": {"c": "is {bar}", "d": "is baz"}}
    variables = {"foo": "::foo", "bar": "::bar"}

    updated_target = transform(target=target, source=source, variables=variables)

    assert target == {"a": "is {foo}", "b": {"c": "is {bar}", "d": "is baz"}}

    assert updated_target["a"] == "is 1"
    assert updated_target["b"]["c"] == "is 2"
    assert updated_target["b"]["d"] == "is baz"


def test_full_transform_with_ignored_paths():
    source = {"general": {"id": "12345", "name": "Mac"}}
    target = {"a": "foo", "b": {"c": "is {bar}", "d": "baz"}}
    updates = {"id": "::general.id", "b.e": "foobar", "'f.g'": 1}
    variables = {"foo": "::foo", "bar": "::bar"}
    ignored_paths = ["b.c", "f"]

    updated_target = transform(
        target=target,
        source=source,
        updates=updates,
        variables=variables,
        ignored_paths=ignored_paths,
    )

    assert "id" not in target
    assert "e" not in target["b"]
    assert "f" not in target

    assert updated_target["a"] == "foo"
    assert updated_target["b"] == {"c": "is None", "d": "baz", "e": "foobar"}
    assert updated_target["id"] == "12345"
    assert "f" not in updated_target

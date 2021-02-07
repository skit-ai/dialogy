import pytest
from dialogy.types.entity.utils import traverse_dict, validate_type


def test_traverse_dict() -> None:
    obj = {"a": {"b": {"c": 10}, "1": {"d": 11}}}
    assert traverse_dict(obj, ["a", "b", "c"]) == 10, "Traversal failed."


def test_traverse_dict_raises_type_error() -> None:
    obj = {"a": {"b": {"c": 10}, "1": {"d": 11}}}
    with pytest.raises(TypeError):
        traverse_dict(obj, ["a", "b", "c", 1])


def test_traverse_dict_raises_key_error():
    obj = {"a": {"b": {"c": 10}, "1": {"d": 11}}}
    with pytest.raises(KeyError):
        traverse_dict(obj, ["a", "k"])


def test_validate_type_raises_error() -> None:
    test_input = "string"
    with pytest.raises(TypeError):
        validate_type(test_input, int)


def test_validate_type_happy_case() -> None:
    test_input = "string"
    result = validate_type(test_input, str)
    assert result is None, "False positives from validate_type"

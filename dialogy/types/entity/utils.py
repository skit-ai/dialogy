"""Module provides utility functions for entities.

Import functions:
    - dict_traversal
    - validate_type
"""
from typing import List, Any, Tuple, Union, Dict
from functools import reduce


def traverse_dict(obj: Dict[Any, Any], properties: List[str]) -> Any:
    """Traverse a dictionary for a given list of properties.

    This is useful for traversing a deeply nested dictionary.
    Instead of recursion, we are using reduce to update the `dict`.
    Missing properties will lead to KeyErrors.

    Args:
        obj (Dict[Any, Any]): The `dict` to traverse.
        properties (List[int]): List of properties expected in the `dict`.

    Raises:
        KeyError: There is a chance of the property list containing elements not present in the `dict`.
        TypeError: There is a chance of the property being accessed over values that are not compatible.

    Returns:
        Any: The value within the `dict` described by the properties list.
    """
    try:
        return reduce(lambda o, k: o[k], properties, obj)
    except KeyError as key_error:
        raise KeyError(
            f"Missing property {key_error} in {obj}. Check the types."
        ) from key_error
    except TypeError as type_error:
        raise TypeError(
            f"The properties aren't describing path within a dictionary. | {type_error}"
        ) from type_error


def validate_type(obj: Any, obj_type: Union[type, Tuple[type]]) -> None:
    """Raise TypeError on object type mismatch.

    This is syntatic sugar for instance type checks.

    The check is by exclusion of types. Wraps exception raising logic.

    Args:
        obj (Any): The object available for type assertion.
        obj_type (Union[type, Tuple[type]]): This must match the type of the object.

    Raises:
        TypeError: If the type `obj_type` doesn't match the type of `obj`.
    """
    if not isinstance(obj, obj_type):
        raise TypeError(f"{obj} should be a {obj_type}")

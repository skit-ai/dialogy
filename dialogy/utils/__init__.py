"""
Module provides utility functions for entities.

Import functions:
    - dict_traversal
    - validate_type
"""
from datetime import datetime
from functools import reduce
from typing import Any, Dict, List, Tuple, Union


def traverse_dict(obj: Dict[Any, Any], properties: List[str]) -> Any:
    """
    Traverse a dictionary for a given list of properties.

    This is useful for traversing a deeply nested dictionary.
    Instead of recursion, we are using reduce to update the `dict`.
    Missing properties will lead to KeyErrors.

    .. ipython:: python
        :okexcept:

        from dialogy.utils import traverse_dict

        input_ = {
            "planets": {
                "mars": [{
                    "name": "",
                    "languages": [{
                        "beep": {"speakers": 11},
                    }, {
                        "bop": {"speakers": 30},
                    }]
                }]
            }
        }
        traverse_dict(input_, ["planets", "mars", 0 , "languages", 1, "bop"])

        # element with index 3 doesn't exist!
        traverse_dict(input_, ["planets", "mars", 0 , "languages", 3, "bop"])

    :param obj: The `dict` to traverse.
    :type obj: Dict[Any, Any]
    :param properties: List of properties to be parsed as a path to be navigated in the `dict`.
    :type properties: List[int]
    :return: A value within a deeply nested dict.
    :rtype: Any
    :raises KeyError: Missing property in the dictionary.
    :raises TypeError: Properties don't describe a path due to possible type error.
    """
    try:
        return reduce(lambda o, k: o[k], properties, obj)
    except KeyError as key_error:
        raise KeyError(
            f"Missing property {key_error} in {obj}. Check the types. Failed for path {properties}"
        ) from key_error
    except TypeError as type_error:
        raise TypeError(
            f"The properties aren't describing path within a dictionary. | {type_error}. Failed for path {properties}"
        ) from type_error


def validate_type(obj: Any, obj_type: Union[type, Tuple[type]]) -> None:
    """
    Raise TypeError on object type mismatch.

        This is syntatic sugar for instance type checks.

        The check is by exclusion of types. Wraps exception raising logic.

        :param obj: An object available for type assertion
        :type obj: Any
        :param obj_type: This must match the type of the object.
        :type obj_type: (Union[type, Tuple[type]])
        :return:
        :rtype:
        :raises TypeError: If the type `obj_type` doesn't match the type of `obj`.
    """
    if not isinstance(obj, obj_type):
        raise TypeError(f"{obj} should be a {obj_type}")


def dt2timestamp(date_time: datetime) -> int:
    """
    Converts a python datetime object to unix-timestamp.

    :param date_time: An instance of datetime.
    :type date_time: datetime
    :return: Unix timestamp integer.
    :rtype: int
    """
    return int(date_time.timestamp() * 1000)

"""
Module provides access to a base class to create other entities. 
This is an unsafe class and not meant for direct use.

These methods of this class that are supposed to be overridden:
- __validate
- get_value

Import classes:
    - BaseEntity
"""
from typing import Any, Dict, List, Optional

import attr

from dialogy.types.plugins import PluginFn


@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
    Do not use it directly in any preprocessing or postprocessing functions.
    Its intended purpose is to define types.

    Attributes:
    - `range` is the character range in the alternative where the entity is parsed.
    - `body` is the string that is extracted.
    - `entity_type` is the type of the entity.
    - `value` is the normalized value of the entity. This can either be a string, an integer or a Dict.
    - `parsers` gives the list of all the functions that have changed this entity.
        This list will be in sorted order, which means that the first element has worked
        on the entity first.
    - `score` is the confidence that the range is the entity.
    - `alternative_index` is the index of transcript within the ASR output: `List[Utterances]`
        from which this entity was picked up. This may be None.
    """

    range       = attr.ib(type=Dict[str, int])
    body        = attr.ib(type=str, validator=attr.validators.instance_of(str))
    entity_type = attr.ib(type=str, validator=attr.validators.instance_of(str))
    parsers     = attr.ib(
        type=List[str],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
    )

    score               = attr.ib(type=Optional[float], default=None)
    alternative_index   = attr.ib(type=Optional[int], default=None)
    latent              = attr.ib(type=bool, default=False)
    values              = attr.ib(type=List[Any], default=attr.Factory(list))

    @classmethod
    def __validate(cls, dict_: Dict[str, Any]) -> None:
        """
        Stub method, raises exception to prevent direct use of this class' instances.
        
        Args:
            dict_ (Dict[str, Any]): Any dictionary with string keys and arbitrarily typed values.

        Raises:
            NotImplementedError: Always. This method should be overridden in each subclass.
        """
        raise NotImplementedError("BaseEntity should not be used directly.")

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> BaseEntity:
        """
        Create an instance of a given class `cls` from a `dict` that complies 
        with attributes of `cls` through its keys and values. 
        Compliance is verified using the `__validate` method. It is expected that each subclass 
        will implement their own flavor of `__validate` to check their respective inputs.

        Returns:
            BaseEntity: Instance of class
        """
        cls.__validate(dict_)
        return cls(**dict_)

    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an entity. This helps in debugging and has no production utility

        Args:
            postprocessor (PluginFn): Plugin function applied to an entity
        """
        self.parsers.append(postprocessor.__name__)

    def get_value(self) -> Any:
        """
        Get value of an entity.

        The structure of an entity conceals the value in different data structures.
        This is sugar for access.

        Raises:
            IndexError: If `values` is not a `list`.
            KeyError: If each element in `values` is not a `dict`.

        Returns:
            Any: Arbitrary return value, subclasses should override and return specific types.
        """
        try:
            return self.values[0]["value"]
        except IndexError as index_error:
            raise IndexError(
                'entity value should be in values[0]["value"]'
            ) from index_error
        except KeyError as key_error:
            raise KeyError(
                'entity value should be in values[0]["value"]'
            ) from key_error

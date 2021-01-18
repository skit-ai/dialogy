"""
Module provides access to a base class to create other entities.

These methods of this class that are supposed to be overridden:
- validate
- get_value

Import classes:
    - BaseEntity
"""
from typing import Any, Dict, List, Optional

import attr
import copy

from dialogy import constants
from dialogy.types.plugins import PluginFn
from dialogy.types.entities.utils import traverse_dict, validate_type


@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
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

    range = attr.ib(type=Dict[str, int])
    body = attr.ib(type=str, validator=attr.validators.instance_of(str))
    dim = attr.ib(type=str, validator=attr.validators.instance_of(str))

    parsers = attr.ib(
        type=List[str],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
    )

    score = attr.ib(type=Optional[float], default=None)
    alternative_index = attr.ib(type=Optional[int], default=None)
    latent = attr.ib(type=bool, default=False)
    values = attr.ib(type=List[Any], default=attr.Factory(list))

    __properties_map = constants.BASE_ENTITY_PROPS

    @classmethod
    def validate(cls, dict_: Dict[str, Any]) -> None:
        for prop, prop_type in cls.__properties_map:
            validate_type(traverse_dict(dict_, prop), prop_type)

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> "BaseEntity":
        """
        Create an instance of a given class `cls` from a `dict` that complies
        with attributes of `cls` through its keys and values.
        Compliance is verified using the `__validate` method. It is expected that each subclass
        will implement their own flavor of `__validate` to check their respective inputs.

        Returns:
            BaseEntity: Instance of class
        """
        cls.validate(dict_)
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

    def copy(self) -> "BaseEntity":
        return copy.deepcopy(self)


def entity_synthesis(entity: BaseEntity, property_: str, value: Any) -> BaseEntity:
    """
    Update a property=`property_` of a BaseEntity, with a given value=`value`.

    Args:
        entity (BaseEntity): The BaseEntity instance to update.
        property_ (str): The attribute of a given entity that should be updated.
        value (Any): The value that should updated.

    Raises:
        TypeError: If `entity` is not a BaseEntity.

    Returns:
        BaseEntity: modified instance of BaseEntity.
    """
    if not isinstance(entity, BaseEntity):
        raise TypeError(f"{entity} has type {type(entity)} expected BaseEntity")
    synthetic_entity = entity.copy()
    setattr(synthetic_entity, property_, value)
    return synthetic_entity

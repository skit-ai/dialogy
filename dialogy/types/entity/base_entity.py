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
from dialogy.types.plugin import PluginFn
from dialogy.types.entity.utils import traverse_dict, validate_type

# = BaseEntity =
@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
    Its intended purpose is to define a base for all entity types.
    """

    # **range**
    #
    # is the character range in the alternative where the entity is parsed.
    range = attr.ib(type=Dict[str, int])

    # **type**
    #
    # is same as dimension or `dim` for now. We may deprecate `dim` and retain only `type`.
    type = attr.ib(type=str, validator=attr.validators.instance_of(str))

    # **body**
    #
    # is the string from which the entity is extracted.
    body = attr.ib(type=str, validator=attr.validators.instance_of(str))

    # **dim**
    #
    # is influenced from Duckling's convention of categorization.
    dim = attr.ib(type=str, validator=attr.validators.instance_of(str))

    # **parsers**
    #
    # gives the trail of all the functions that have changed this entity in the sequence of application.
    parsers = attr.ib(
        type=List[str],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
    )

    # **score**
    #
    # is the confidence that the range is the entity.
    score = attr.ib(type=Optional[float], default=None)

    # **slot_names**
    #
    # Entities have awareness of the slots they should fill.
    slot_names = attr.ib(type=List[str], default=attr.Factory(list))

    # **alternative_index**
    #
    # is the index of transcript within the ASR output: `List[Utterances]`
    # from which this entity was picked up. This may be None.
    alternative_index = attr.ib(type=Optional[int], default=None)

    # **latent**
    #
    # Duckling influenced attribute, tells if there is less evidence for an entity if latent is True.
    latent = attr.ib(type=bool, default=False)

    # **values**
    #
    # The parsed value of an entity resides within this attribute.
    values = attr.ib(type=List[Any], default=attr.Factory(list))

    __properties_map = constants.BASE_ENTITY_PROPS

    # == validate ==
    @classmethod
    def validate(cls, dict_: Dict[str, Any]) -> None:
        """
        Check attributes of instance match expected types.

        Args:
            dict_ (Dict[str, Any]): A `Dict` where each key is an attribute of the instance and value is the expected type.
        """
        for prop, prop_type in cls.__properties_map:
            validate_type(traverse_dict(dict_, prop), prop_type)

    # == from_dict ==
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

    # == add_parser ==
    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an entity. This helps in debugging and has no production utility

        Args:
            postprocessor (PluginFn): Plugin function applied to an entity
        """
        self.parsers.append(postprocessor.__name__)

    # == get_value ==
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

    # == copy ==
    def copy(self) -> "BaseEntity":
        """
        Create a deep copy of the instance and return.

        This is needed to prevent mutation of an original entity.
        """
        return copy.deepcopy(self)


# = entity_synthesis =
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

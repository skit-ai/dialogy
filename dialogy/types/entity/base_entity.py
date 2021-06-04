"""
.. _base_entity:
Module provides access to a base class to create other entities.

These methods of this class that are supposed to be overridden:
- validate
- get_value

Import classes:

- BaseEntity
"""
import copy
from typing import Any, Dict, List, Optional

import attr

from dialogy import constants as const
from dialogy.types.plugin import PluginFn
from dialogy.utils import traverse_dict, validate_type


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
    range = attr.ib(type=Dict[str, int], repr=False)

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
    dim = attr.ib(type=Optional[str], default=None, repr=False)

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
    slot_names = attr.ib(type=List[str], default=attr.Factory(list), repr=False)

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
    values = attr.ib(
        type=List[Dict[str, Any]],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(List),
        repr=False,
    )

    # **values**
    #
    # A single value interpretation from values.
    value: Any = attr.ib(default=None)

    # **entity_type**
    #
    # Mirrors type, to be deprecated.
    entity_type: Optional[str] = attr.ib(default=None, repr=False)

    __properties_map = const.BASE_ENTITY_PROPS

    def __attrs_post_init__(self) -> None:
        self.entity_type = self.type

    @classmethod
    def validate(cls, dict_: Dict[str, Any]) -> None:
        """
        Check attributes of instance match expected types.

        :param dict_: A `Dict` where each key is an attribute of the instance and value is the expected type.
        :type dict_: Dict[str, Any]
        :return: None
        :rtype: None
        """
        for prop, prop_type in cls.__properties_map:
            validate_type(traverse_dict(dict_, prop), prop_type)

    @classmethod
    def reshape(cls, dict_: Dict[str, Any]) -> Dict[str, Any]:
        """
        :type dict_: Dict[str, Any]
        """
        match_start = dict_[const.EntityKeys.START]
        match_end = dict_[const.EntityKeys.END]

        dict_[const.EntityKeys.RANGE] = {
            const.EntityKeys.START: match_start,
            const.EntityKeys.END: match_end,
        }
        # ['body', 'start', 'value', 'end', 'dim', 'latent']

        # **type** of an entity is same as its **dimension**.
        dict_[const.EntityKeys.TYPE] = dict_[const.EntityKeys.DIM]

        # This piece is a preparation for multiple entity values.
        # So, even though we are confident of the value found, we are still keeping the
        # structure.
        if const.EntityKeys.VALUES in dict_[const.EntityKeys.VALUE]:
            dict_[const.EntityKeys.VALUES] = dict_[const.EntityKeys.VALUE][
                const.EntityKeys.VALUES
            ]
        else:
            dict_[const.EntityKeys.VALUES] = [dict_[const.EntityKeys.VALUE]]

        del dict_[const.EntityKeys.START]
        del dict_[const.EntityKeys.END]
        del dict_[const.EntityKeys.VALUE]
        return dict_

    @classmethod
    def from_dict(cls, dict_: Dict[str, Any]) -> "BaseEntity":
        """
        Create an instance of a given class `cls` from a `dict` that complies
        with attributes of `cls` through its keys and values.
        Compliance is verified using the `__validate` method. It is expected that each subclass
        will implement their own flavor of `__validate` to check their respective inputs.

        :param dict_: A dict that provides all the attributes necessary for instantiating this class
        :type dict_: Dict[str, Any]
        :return: Instance of class
        :rtype: BaseEntity
        """
        dict_ = cls.reshape(dict_)
        cls.validate(dict_)
        return cls(**dict_)

    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an entity. This helps in debugging and has no production utility

        :param postprocessor: Plugin function applied to an entity
        :type postprocessor: PluginFn
        :return: None
        :rtype: None
        """
        self.parsers.append(postprocessor.__name__)

    def get_value(self, reference: Any = None) -> Any:
        """
        Get value of an entity.

        The structure of an entity conceals the value in different data structures.
        This is sugar for access.

        :param reference: Picking value/values from a reference object.
        :type reference: Any
        :raises IndexError: If `values` is not a `list`.
        :raises KeyError: If each element in `values` is not a `dict`.
        :return: Arbitrary instance, subclasses should override and return specific types.
        :rtype: BaseEntity
        """
        key = "value"
        error_message = f'entity value should be in values[0]["{key}"]'
        if not reference:
            try:
                return self.values[0][key]
            except IndexError as index_error:
                raise IndexError(error_message) from index_error
            except KeyError as key_error:
                raise KeyError(error_message) from key_error
        else:
            return reference.get(const.VALUE)

    def copy(self) -> "BaseEntity":
        """
        Create a deep copy of the instance and return.

        This is needed to prevent mutation of an original entity.
        :return: A copy of BaseEntity that calls this method.
        :rtype: BaseEntity
        """
        return copy.deepcopy(self)

    def json(
        self, skip: Optional[List[str]] = None, add: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.

        Applies some expected filters to prevent information bloat.

        Add section for skipping more properties using const.SKIP_ENTITY_ATTRS + [""]

        :param skip: Names of attributes that should not be included while converting to a dict.
            Defaults to None.
        :type skip: Optional[List[str]]
        :param add: Names of attributes that should be included while converting to a dict.
            Defaults to None.
        :type add: Optional[List[str]]
        :return: Dictionary representation of the object
        :rtype: Dict[str, Any]
        """
        skip_ = skip or const.SKIP_ENTITY_ATTRS
        if add and isinstance(add, list):
            skip_ = [name for name in const.SKIP_ENTITY_ATTRS if name not in add]
        return attr.asdict(self, filter=lambda attr, _: attr.name not in skip_)

    def set_value(self, value: Any = None) -> "BaseEntity":
        """
        Set values and value attribute.

        :param value: The parsed value of an entity token.
        :type value: Any
        :return: None
        :rtype: None
        """
        if value is None and isinstance(self.values, list) and len(self.values) > 0:
            self.value = self.values[0][const.VALUE]
        else:
            self.values = [{const.VALUE: value}]
            self.value = value
        return self


# = entity_synthesis =
def entity_synthesis(entity: BaseEntity, property_: str, value: Any) -> BaseEntity:
    """
    Update a property=`property_` of a BaseEntity, with a given value=`value`.

    .. warning:: This is an unsafe method. Use with caution as it doesn't check the type of
        the new value being type safe.

    :param entity: A BaseEntity instance.
    :type entity: BaseEntity
    :param property_: An attribute of BaseEntity that should be changed.
    :type property_: str
    :param value: The value to replace within a BaseEntity instance.
    :type value: Any
    :return: A copy of BaseEntity instance used in this function with modifications.
    :rtype: BaseEntity
    """
    if not isinstance(entity, BaseEntity):
        raise TypeError(f"{entity} has type {type(entity)} expected BaseEntity")
    synthetic_entity = entity.copy()
    setattr(synthetic_entity, property_, value)
    return synthetic_entity

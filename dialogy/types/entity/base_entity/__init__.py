"""
.. _BaseEntity:

Module provides access to a base class to create other entities.
"""
from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Union

import attr

from dialogy import constants as const


# = BaseEntity =
@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
    Its intended purpose is to define a base for all entity types.
    """

    range: Dict[str, int] = attr.ib(repr=False, order=False, kw_only=True)
    """
    The location of an entity marked via start and end indices on the string.

    .. code:: python

        body = "i'll come by 4 pm"
        entity = "4 pm"
        range = {"start": 13, "end": 17}
    """

    body: str = attr.ib(validator=attr.validators.instance_of(str), order=False)
    """
    The string from which the entity is extracted.
    """

    dim: Optional[str] = attr.ib(default=None, repr=False, order=False)
    """
    Influenced from Duckling's convention of dimensions.
    """

    type: str = attr.ib(default="value", order=False, kw_only=True)
    """
    One of "value" or "interval".
    """

    parsers: List[str] = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
        order=False,
    )
    """
    The trail of all the functions that have created/updated this entity at any point.
    """

    # **score**
    #
    # is 
    score: Optional[float] = attr.ib(default=None)
    """
    A positive real number that describes the confidence that the range contains the correct entity.
    A value between 0 and 1.
    """

    # **alternative_index**
    #
    alternative_index: Optional[int] = attr.ib(default=None, order=False)
    """
    The index of transcript within the ASR output: `List[Utterances]`
    from which this entity was picked up. This may be None if the entity was generated
    from a different sources.
    """

    alternative_indices: Optional[List[int]] = attr.ib(default=None, order=False)

    latent: bool = attr.ib(default=False, order=False)
    """
    Duckling influenced attribute, :code:`True` means this entity's type wasn't a strict match.
    Example: "may" is latent hint for a month in English, because it is also a modal.
    """
    
    # The parsed value of an entity resides within this attribute.
    values: List[Dict[str, Any]] = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.optional(attr.validators.instance_of(list)),  # type: ignore
        repr=False,
        order=False,
    )
    """
    Duckling stores value of an entity within a list for some types. We try to keep that as a standard for
    all entities.
    """

    value: Any = attr.ib(default=None, order=False)
    """
    A single value interpretation from values.
    """
    
    # **entity_type**
    entity_type: Optional[str] = attr.ib(default=None, repr=False, order=False)
    """
    Describes the type of the value of an entity. Could be one of "time", "date", "people", "number", etc.
    """

    def __attrs_post_init__(self) -> None:
        if self.values and not self.value:
            self.value = self.values[0][const.VALUE]
        elif self.value and not self.values:
            self.values = [{const.VALUE: self.value}]

    def add_parser(self, plugin: Union[Any, str]) -> "BaseEntity":
        """
        Update parsers with the postprocessor function name

        This is to identify the progression in which the plugins were applied to an entity.
        This only helps in debugging and has no production utility.

        :param plugin: The class that modifies this instance. Preferably should be a plugin.
        :type plugin: Plugin
        :return: Calling instance with modifications to :code:`parsers` attribute.
        :rtype: BaseEntity
        """
        self.parsers.append(str(plugin))
        return self

    def get_value(self) -> Any:
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
        try:
            return self.values[0][key]
        except IndexError as index_error:
            raise IndexError(error_message) from index_error

    def copy(self) -> BaseEntity:
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

    @classmethod
    def from_dict(
        cls, dict_: Dict[str, Any], reference: Optional[BaseEntity] = None
    ) -> BaseEntity:
        """
        Deserializer

        :param dict_: A dictionary that describes attributes of an entity within its keys. At least partially.
        :type dict_: Dict[str, Any]
        :param reference: An instance that should be used for retaining other attributes, defaults to None
        :type reference: Optional[BaseEntity], optional
        :return: A new :ref:`BaseEntity<BaseEntity>
        :rtype: BaseEntity
        """
        if reference:
            if const.VALUES in dict_ or const.VALUE in dict_:
                object.__setattr__(reference, const.VALUES, None)
                object.__setattr__(reference, const.VALUE, None)
            return attr.evolve(reference, **dict_)
        return cls(**dict_)


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

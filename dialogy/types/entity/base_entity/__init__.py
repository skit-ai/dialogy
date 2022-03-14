"""
.. _BaseEntity:

Module provides access to a base class to create other entities.


.. mermaid::

    classDiagram
        direction LR
        BaseEntity --|> NumericalEntity
        BaseEntity --|> CreditCardNumberEntity
        BaseEntity --|> CurrencyEntity    
        BaseEntity --|> TimeEntity
        BaseEntity --|> KeywordEntity
        BaseEntity --|> DurationEntity
        BaseEntity --|> PeopleEntity

        TimeEntity --|> TimeIntervalEntity

        NumericalEntity ..> TimeEntity: as_time
        DurationEntity ..> TimeEntity: as_time

        class BaseEntity {
            +Dict[str, int] range
            +str body
            +str dim
            +int alternative_index
            +str type
            +str entity_type
            +float score
            +Any value
            +List~Any~ values
            +List~str~ parsers
            +bool latent
            +Any get_value()
            +Dict[str, Any] json()
            $BaseEntity from_dict(d)
        }

        class CurrencyEntity {
            +str unit
            +Any get_value()
            +CurrencyEntity from_duckling(d)
        }

        class CreditCardNumberEntity {
            +str issuer
            +from_duckling(d: dict, idx: int)
            +CreditCardNumberEntity from_duckling(d)
        }

        class KeywordEntity {
        }

        class DurationEntity {
            +str unit
            +dict normalized
            +DurationEntity from_duckling(d)
        }

        class NumericalEntity {
            +NumericalEntity from_duckling(d)
        }

        class PeopleEntity {
            +str unit
            +PeopleEntity from_duckling(d)
        }

        class TimeEntity {
            +str grain
            +datetime get_value()
            +TimeEntity from_duckling(d)
        }

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

    # **range**
    #
    # is the character range in the alternative where the entity is parsed.
    range: Dict[str, int] = attr.ib(repr=False, order=False, kw_only=True)

    # **body**
    #
    # is the string from which the entity is extracted.
    body: str = attr.ib(validator=attr.validators.instance_of(str), order=False)

    # **dim**
    #
    # is influenced from Duckling's convention of categorization.
    dim: Optional[str] = attr.ib(default=None, repr=False, order=False)

    # **type**
    #
    # is same as dimension or `dim` for now. We may deprecate `dim` and retain only `type`.
    type: str = attr.ib(default="value", order=False, kw_only=True)

    # **parsers**
    #
    # gives the trail of all the functions that have changed this entity in the sequence of application.
    parsers: List[str] = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
        order=False,
    )

    # **score**
    #
    # is the confidence that the range is the entity.
    score: Optional[float] = attr.ib(default=None)

    # **alternative_index**
    #
    # is the index of transcript within the ASR output: `List[Utterances]`
    # from which this entity was picked up. This may be None.
    alternative_index: Optional[int] = attr.ib(default=None, order=False)
    alternative_indices: Optional[List[int]] = attr.ib(default=None, order=False)

    # **latent**
    #
    # Duckling influenced attribute, tells if there is less evidence for an entity if latent is True.
    latent: bool = attr.ib(default=False, order=False)

    # **values**
    #
    # The parsed value of an entity resides within this attribute.
    values: List[Dict[str, Any]] = attr.ib(
        default=attr.Factory(list),
        validator=attr.validators.optional(attr.validators.instance_of(list)),  # type: ignore
        repr=False,
        order=False,
    )

    # **values**
    #
    # A single value interpretation from values.
    value: Any = attr.ib(default=None, order=False)

    # **entity_type**
    entity_type: Optional[str] = attr.ib(default=None, repr=True, order=False)

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
        if reference:
            if const.VALUES in dict_ or const.VALUE in dict_:
                object.__setattr__(reference, const.VALUES, None)
                object.__setattr__(reference, const.VALUE, None)
            return attr.evolve(reference, **dict_)
        return cls(**dict_)

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int, **kwargs: Any
    ) -> BaseEntity:
        raise NotImplementedError  # pragma: no cover


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

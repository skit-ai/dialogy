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
            +str grain
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

from dialogy import constants as const

from pydantic import BaseModel, Field


# = BaseEntity =
class BaseEntity(BaseModel):
    """
    Base Entity Type.

    This class is meant for subclassing.
    Its intended purpose is to define a base for all entity types.
    """

    # **range**
    #
    # is the character range in the alternative where the entity is parsed.
    range: Dict[str, int]

    # **body**
    #
    # is the string from which the entity is extracted.
    body: str

    # **dim**
    #
    # is influenced from Duckling's convention of categorization.
    dim: Optional[str] = None

    # **type**
    #
    # is same as dimension or `dim` for now. We may deprecate `dim` and retain only `type`.
    type: str = "value"

    # **parsers**
    #
    # gives the trail of all the functions that have changed this entity in the sequence of application.
    parsers: List[str] = Field(default_factory=list)

    # **score**
    #
    # is the confidence that the range is the entity.
    score: Optional[float] = None

    # **alternative_index**
    #
    # is the index of transcript within the ASR output: `List[Utterances]`
    # from which this entity was picked up. This may be None.
    alternative_index: Optional[int] = None
    alternative_indices: Optional[List[int]] = None

    # **latent**
    #
    # Duckling influenced attribute, tells if there is less evidence for an entity if latent is True.
    latent: bool = False

    # **values**
    #
    # The parsed value of an entity resides within this attribute.
    values: List[Dict[str, Any]] = Field(default_factory=list)

    # **values**
    #
    # A single value interpretation from values.
    value: Any = None

    # **entity_type**
    entity_type: Optional[str] = None

    def __init__(self, **data):  # type: ignore
        if (
            "values" in data
            and data["values"]
            and ("value" not in data or not data["value"])
        ):
            data["value"] = data["values"][0][const.VALUE]
        elif (
            "value" in data
            and data["value"]
            and ("values" not in data or not data["values"])
        ):
            data["values"] = [{const.VALUE: data["value"]}]

        if "meta" in data and isinstance(data["meta"], dict):
            for k, v in data["meta"].items():
                if k not in data:
                    data[k] = v

        super().__init__(**data)

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

    @classmethod
    def from_dict(
        cls, dict_: Dict[str, Any], reference: Optional[BaseEntity] = None
    ) -> BaseEntity:
        if reference:
            if const.VALUES in dict_ or const.VALUE in dict_:
                object.__setattr__(reference, const.VALUES, None)
                object.__setattr__(reference, const.VALUE, None)
            return reference.copy(update=dict_, deep=True)
        return cls(**dict_)

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int, **kwargs: Any
    ) -> Optional[BaseEntity]:
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

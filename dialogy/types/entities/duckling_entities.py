"""Entity Types from Duckling
"""

import dateutil.parser
from typing import Any, List, Optional, Dict, Callable, TypeVar
from datetime import datetime, timedelta
from functools import reduce

import attr
import pytz
import copy
import operator as op

from dialogy.types.entities import BaseEntity
from dialogy.types.entities.utils import op_set, object_return, validate_type

RefTime = int


@attr.s
class NumericalEntity(BaseEntity):
    """Numerical Entity Type

    Keys are:
        - `dim` dimension of the entity from duckling parser
        - `values` values is a List which contains the actual value of the entity
        - `reader` gives the list of all functions that have changed the entity in some way
        - `type` is the type of the entity which can have values in ["value", "interval"]
    """

    dim = attr.ib(type=str, default=attr.Factory(str))
    values = attr.ib(type=List[Dict[str, Any]], default=attr.Factory(list))
    reader = attr.ib(type=List[Callable[[Any], Any]], default=attr.Factory(list))
    type = attr.ib(
        type=str, default="value", validator=attr.validators.instance_of(str)
    )
    __properties_map = [
        (["range"], dict),
        (["range", "start"], int),
        (["range", "end"], int),
        (["body"], str),
        (["values"], list),
        (["dim"], str),
        (["latent"], bool),
        (["entity_type"], str),
    ]

    def get_value(self) -> Any:
        """returns the value of the entity in values.

        Ues this function to get the value of the entity

        Raises:
            KeyError: raises a KeyError when there is no property `value` in `values`

        Returns:
            Any: Returns the value of the entity
        """
        try:
            return self.values[0]["value"]
        except KeyError as key_error:
            raise KeyError("value should be a key in value") from key_error

    @classmethod
    def __validate(cls, dict_: Dict[str, Any]) -> None:
        for prop, prop_type in cls.__properties_map:
            validate_type(object_return(dict_, prop), prop_type)


def mutate_numerical_entity(
    entity: NumericalEntity, property_: str, value: Any
) -> NumericalEntity:
    """Takes in an entity, a property and a value and sets the property of the object as the value

    Args:
        entity (NumericalEntity): [description]
        property_ (str): [description]
        value (Any): [description]

    Raises:
        TypeError: [description]

    Returns:
        NumericalEntity: [description]
    """
    if not isinstance(entity, NumericalEntity):
        raise TypeError(f"{entity} has type {type(entity)} expected NumericalEntity")
    setattr(entity, property_, value)
    return entity


@attr.s
class TimeEntity(NumericalEntity):
    """
    Date, Time and Datetime Entity types

    Keys are:
    - `grain` tells us the smallest unit of time in the utterance
    """

    grain = attr.ib(type=str, default=None, validator=attr.validators.instance_of(str))
    __properties_map = [
        (["range"], dict),
        (["range", "start"], int),
        (["range", "end"], int),
        (["body"], str),
        (["values"], list),
        (["dim"], str),
        (["latent"], bool),
        (["grain"], str),
        (["entity_type"], str),
    ]

    def __copy_entity(self) -> "TimeEntity":
        return copy.deepcopy(self)

    def filter(self, ref_time: datetime, operator: str) -> Optional["TimeEntity"]:
        """
        Creates a TimeEntity with values according to the the operator functions
        NOTE: `ref_time` needs to be of offset-aware (timezoned) datetime type

        Returns:
            TimeEntity: returns a new instance of the class with the updated values
        """
        # NOTE: We assume some delay in processing, so take out 5 seconds from ref_time
        ref_time = ref_time - timedelta(0, 5)
        updated_entity = self.__copy_entity()
        op_set: Dict[str, Callable[[Dict[str, Any], datetime], bool]]
        filtered_values = [
            date_info
            for date_info in updated_entity.values
            if op_set[operator](date_info, ref_time)
        ]

        if not filtered_values:
            return None
        mutate_numerical_entity(updated_entity, "values", filtered_values)
        return updated_entity


@attr.s
class TimeIntervalEntity(TimeEntity):
    """
    Datetime Interval Entity Type

    Keys:
    - `type`
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """

    type = attr.ib(type=str, default="interval")
    __properties_map = [
        (["range"], dict),
        (["range", "start"], int),
        (["range", "end"], int),
        (["body"], str),
        (["values"], list),
        (["dim"], str),
        (["latent"], bool),
        (["grain"], str),
        (["entity_type"], str),
    ]


@attr.s
class PeopleEntity(NumericalEntity):
    """
    People Entity
    """

    unit = attr.ib(
        type=str, default=attr.Factory(str), validator=attr.validators.instance_of(str)
    )
    __properties_map = [
        (["range"], dict),
        (["range", "start"], int),
        (["range", "end"], int),
        (["body"], str),
        (["values"], list),
        (["dim"], str),
        (["latent"], bool),
        (["entity_type"], str),
        (["unit"], str),
    ]

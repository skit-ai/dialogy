from typing import Any, Dict, List, Optional, Union

import attr

from dialogy import constants as const
from dialogy.types.entity import BaseEntity
from dialogy.utils import traverse_dict, validate_type


@attr.s
class PlasticCurrencyEntity(BaseEntity):
    body = attr.ib(type=str, validator=attr.validators.instance_of(str), default=None)
    range = attr.ib(type=Dict[str, int], repr=False, default=None)
    type = attr.ib(
        type=str, validator=attr.validators.instance_of(str), default="plastic-money"
    )
    value: Any = attr.ib(default=None)

    latent = attr.ib(type=bool, default=False)
    dim = attr.ib(type=Optional[str], default=None, repr=False)
    score = attr.ib(type=Optional[float], default=None)
    parsers = attr.ib(
        type=List[str],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(list),
    )
    alternative_index = attr.ib(type=Optional[int], default=None)
    alternative_indices = attr.ib(type=Optional[List[int]], default=None)
    entity_type: Optional[str] = attr.ib(repr=False, default="plastic-money")

    __properties_map = const.PLASTIC_MONEY_PROPS

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

        del dict_[const.EntityKeys.START]
        del dict_[const.EntityKeys.END]
        return dict_

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
        return (
            self.value.get(const.VALUE) if not reference else reference.get(const.VALUE)
        )

    def set_value(self, value: Any = None) -> BaseEntity:
        """
        Set values and value attribute.

        :param value: The parsed value of an entity token.
        :type value: Any
        :return: None
        :rtype: None
        """
        if not isinstance(value, dict):
            raise TypeError(f"{value} is not a dict.")
        if const.VALUE not in value:
            raise KeyError(f"{const.VALUE} is not in {value}.")
        if const.EntityKeys.ISSUER not in value:
            raise KeyError(f"{const.EntityKeys.ISSUER} is not in {value}.")
        self.value = value
        return self

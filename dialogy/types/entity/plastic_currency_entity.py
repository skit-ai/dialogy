from typing import Dict, List, Optional, Any, Union

import attr

from dialogy.types.entity import BaseEntity
from dialogy import constants as const
from dialogy.utils import traverse_dict, validate_type


@attr.s
class PlasticCurrencyEntity(BaseEntity):
    body = attr.ib(type=str, validator=attr.validators.instance_of(str), default=None)
    range = attr.ib(type=Dict[str, int], repr=False, default=None)
    type = attr.ib(type=str, validator=attr.validators.instance_of(str), default=None)
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
    entity_type: Optional[str] = attr.ib(default=None, repr=False)

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

    def add_parser(self, plugin: type) -> "BaseEntity":
        """
        Update parsers with the postprocessor function name

        This is to identify the progression in which the plugins were applied to an entity.
        This only helps in debugging and has no production utility.

        :param plugin: The class that modifies this instance. Preferably should be a plugin.
        :type plugin: Plugin
        :return: Calling instance with modifications to :code:`parsers` attribute.
        :rtype: BaseEntity
        """
        self.parsers.append(plugin.__name__)
        return self

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
        if reference:
            return reference.get(const.VALUE)
        return self.value.get(const.VALUE)

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
        self.value = value
        return self

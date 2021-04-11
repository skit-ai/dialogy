"""
.. _people_entity:
Module provides access to entity types that can be parsed to obtain numeric values specific to denote people.

Import classes:
    - PeopleEntity
"""
import attr

from dialogy import constants
from dialogy.types.entity.numerical_entity import NumericalEntity


@attr.s
class PeopleEntity(NumericalEntity):
    """
    A variant of numerical entity which addresses collections of people.

    Example sentences that contain the entity are:
    - "N people", where N is a whole number.
    - "A couple" ~ 2 people.
    - "I have triplets" ~ 3 children.
    """

    unit = attr.ib(type=str, default="", validator=attr.validators.instance_of(str))
    __properties_map = constants.PEOPLE_ENTITY_PROPS

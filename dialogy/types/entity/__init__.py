"""
Module provides access to entity types.

We are explicitly supporting entities known for Duckling, any new entity support
will be added depending on open issues.
"""
from typing import Any, Dict

from dialogy.types.entity.base_entity import BaseEntity, entity_synthesis
from dialogy.types.entity.credit_card_number import CreditCardNumberEntity
from dialogy.types.entity.amount_of_money import CurrencyEntity
from dialogy.types.entity.duration import DurationEntity
from dialogy.types.entity.keyword import KeywordEntity
from dialogy.types.entity.location_entity import LocationEntity
from dialogy.types.entity.numerical import NumericalEntity
from dialogy.types.entity.people import PeopleEntity
from dialogy.types.entity.time import TimeEntity
from dialogy.types.entity.time_interval import TimeIntervalEntity

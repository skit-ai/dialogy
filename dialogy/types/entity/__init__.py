"""
Module provides access to entity types.

We are explicitly supporting entities known for Duckling, any new entity support
will be added depending on open issues.
"""
from typing import Any, Dict

from dialogy.types.entity.base_entity import BaseEntity, entity_synthesis
from dialogy.types.entity.credit_card_number_entity import CreditCardNumberEntity
from dialogy.types.entity.currency_entity import CurrencyEntity
from dialogy.types.entity.duration_entity import DurationEntity
from dialogy.types.entity.keyword_entity import KeywordEntity
from dialogy.types.entity.location_entity import LocationEntity
from dialogy.types.entity.numerical_entity import NumericalEntity
from dialogy.types.entity.people_entity import PeopleEntity
from dialogy.types.entity.time_entity import TimeEntity
from dialogy.types.entity.time_interval_entity import TimeIntervalEntity

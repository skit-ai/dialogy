from typing import Dict, Any, Union, Optional

from dialogy import constants as const
from dialogy.types.entity.numerical_entity import NumericalEntity
from dialogy.types.entity.currency_entity import CurrencyEntity
from dialogy.types.entity.duration_entity import DurationEntity
from dialogy.types.entity.people_entity import PeopleEntity
from dialogy.types.entity.time_entity import TimeEntity
from dialogy.types.entity.time_interval_entity import TimeIntervalEntity
from dialogy.types.entity.credit_card_number_entity import CreditCardNumberEntity


def deserialize_duckling_entity(duckling_entity_dict: Dict[str, Any], alternative_index: int, reference_time: Optional[int] = None) -> Union[NumericalEntity, CurrencyEntity, DurationEntity, PeopleEntity, TimeEntity, TimeIntervalEntity, CreditCardNumberEntity]:
    keys = tuple(sorted(duckling_entity_dict.keys()))
    if keys != const.DUCKLING_ENTITY_KEYS:
        raise ValueError(f"Invalid Duckling entity keys: {keys} expected {const.DUCKLING_ENTITY_KEYS}.")

    dimension = duckling_entity_dict[const.DIM]
    if dimension not in const.DUCKLING_DIMS:
        raise ValueError(f"Invalid Duckling dimension: {dimension} expected {const.DUCKLING_DIMS}.")

    value_keys = tuple(sorted(duckling_entity_dict[const.VALUE].keys()))

    if dimension == const.PEOPLE:
        return PeopleEntity.from_duckling(duckling_entity_dict, alternative_index)

    elif dimension == const.TIME:
        if value_keys == const.DUCKLING_TIME_VALUES_ENTITY_KEYS:
            return TimeEntity.from_duckling(duckling_entity_dict, alternative_index)

        elif dimension == const.TIME and value_keys in const.DUCKLING_TIME_INTERVAL_ENTITY_KEYS:
            return TimeIntervalEntity.from_duckling(duckling_entity_dict, alternative_index)

        else:
            raise ValueError(f"Dimension {const.TIME} recieved invalid keys {value_keys} expected either {const.DUCKLING_TIME_VALUES_ENTITY_KEYS} or {const.DUCKLING_TIME_INTERVAL_ENTITY_KEYS}.")

    elif dimension == const.AMOUNT_OF_MONEY:
        return CurrencyEntity.from_duckling(duckling_entity_dict, alternative_index)

    elif dimension == const.NUMBER:
        return NumericalEntity.from_duckling(duckling_entity_dict, alternative_index)

    elif dimension == const.DURATION:
        return DurationEntity.from_duckling(duckling_entity_dict, alternative_index)

    else: # dimension == const.CREDIT_CARD_NUMBER:
        return CreditCardNumberEntity.from_duckling(duckling_entity_dict, alternative_index)

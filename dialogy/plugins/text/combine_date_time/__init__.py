from typing import Any, Dict, List, Optional

import attr
from pydash import py_

from dialogy import constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import BaseEntity, TimeEntity


def has_time_component(entity: BaseEntity) -> bool:
    return entity.entity_type in [
        CombineDateTimeOverSlots.TIME,
        CombineDateTimeOverSlots.DATETIME,
    ]


def is_date(entity: BaseEntity) -> bool:
    return entity.entity_type == CombineDateTimeOverSlots.DATE


class CombineDateTimeOverSlots(Plugin):
    """

    .. _CombineDateTimeOverSlots:

    Dialog case:

    Assume that at the moment of dialog the date is 15th December 2019.

    +---+------+----------------------------+-------------------------------------------------------+
    |   |      |          utterance         |                         entity                        |
    +===+======+============================+=======================================================+
    | 1 | BOT  | When do you want to visit? |                                                       |
    +---+------+----------------------------+-------------------------------------------------------+
    | 2 | USER | Day after tomorrow         |        {'type': 'date', 'value': '2019-12-17'}        |
    +---+------+----------------------------+-------------------------------------------------------+
    | 3 | BOT  | At what time?              |                                                       |
    +---+------+----------------------------+-------------------------------------------------------+
    | 4 | USER | 3 pm                       | {'type': 'time', 'value': '2019-12-15T15:00:00+0000'} |
    +---+------+----------------------------+-------------------------------------------------------+

    We want to use the slots such that the date from interaction [2] and the time from interaction [4] are combined into a single entity.

    We receive this as a tracked slot:

    .. code-block:: json

        [{
            "name": "_callback_",
            "slots": [{
                "name": "callback_datetime",
                "type": [
                    "time",
                    "date",
                    "datetime"
                ],
                "values": [{
                    "alternative_index": 0,
                    "body": "tomorrow",
                    "entity_type": "date",
                    "grain": "day",
                    "parsers": ["duckling"],
                    "range": {
                        "end": 8,
                        "start": 0
                    },
                    "score": null,
                    "type": "value",
                    "value": "2021-10-15T00:00:00+05:30"
                }]
            }]
        }]

    At interaction [4] we would have a TimeEntity from DucklingPlugin but as we can see, the tracked slot provides us
    previously filled values as json.

    So we need to parse the first value in the slot (since they are the entities) if they are one of these date, time, datetime types.
    This would give us a date / time entity that we can subsequently combine with the available entity in the current turn.
    """

    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SUPPORTED_ENTITIES = [DATE, TIME, DATETIME]

    def __init__(
        self,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        replace_output: bool = True,
        use_transform: bool = False,
        trigger_intents: Optional[List[str]] = None,
        debug: bool = False,
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            replace_output=replace_output,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )
        self.trigger_intents = trigger_intents

    def join(
        self, current_entity: TimeEntity, previous_entity: TimeEntity
    ) -> BaseEntity:
        current_turn_datetime = current_entity.get_value()
        previous_turn_datetime = previous_entity.get_value()

        if is_date(current_entity) and has_time_component(previous_entity):
            combined_value = current_turn_datetime.replace(
                hour=previous_turn_datetime.hour,
                minute=previous_turn_datetime.minute,
                second=previous_turn_datetime.second,
            )
        elif is_date(previous_entity) and has_time_component(current_entity):
            combined_value = current_turn_datetime.replace(
                year=previous_turn_datetime.year,
                month=previous_turn_datetime.month,
                day=previous_turn_datetime.day,
            )
        else:
            return current_entity
        return TimeEntity.from_dict(
            {const.VALUE: combined_value.isoformat()}, current_entity
        )

    def get_tracked_slots(
        self, slot_tracker: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        if not self.trigger_intents or not slot_tracker:
            return []

        tracked_intents = [
            intent
            for intent in slot_tracker
            if intent[const.NAME] in self.trigger_intents
        ]

        if not tracked_intents:
            return []

        tracked_intent, *_ = tracked_intents
        return tracked_intent.get(const.SLOTS, [])

    def pick_previously_filled_time_entity(
        self, tracked_slots: Optional[List[Dict[str, Any]]]
    ) -> Optional[TimeEntity]:
        if not tracked_slots:
            return None

        filled_entities_json = tracked_slots[0][const.VALUES]

        if not filled_entities_json or not isinstance(filled_entities_json, list):
            return None

        filled_entity_json, *_ = filled_entities_json
        filled_entity_json[const.VALUES] = [
            {const.VALUE: filled_entity_json[const.VALUE]}
        ]

        return TimeEntity(**filled_entity_json)

    def combine_time_entities_from_slots(
        self, slot_tracker: Optional[List[Dict[str, Any]]], entities: List[BaseEntity]
    ) -> List[BaseEntity]:
        """
        Combines the time entities from the slots with the entities from the current turn.

        .. _combinetimeentitiesfromslots:

        :param slot_tracker: The slot tracker from the previous turn.
        :type slot_tracker: Optional[List[Dict[str, Any]]]
        :param entities: Entities found in the current turn.
        :type entities: List[BaseEntity]
        :return: Combined set of entities.
        :rtype: List[BaseEntity]
        """
        previously_filled_time_entity = self.pick_previously_filled_time_entity(
            self.get_tracked_slots(slot_tracker)
        )

        if not previously_filled_time_entity:
            return entities

        time_entities, other_entities = py_.partition(
            entities,
            lambda entity: entity.entity_type
            in CombineDateTimeOverSlots.SUPPORTED_ENTITIES,
        )
        combined_time_entities = [
            self.join(entity, previously_filled_time_entity) for entity in time_entities
        ]
        return combined_time_entities + other_entities

    def utility(self, input: Input, output: Output) -> List[BaseEntity]:
        """
        Combine the date and time entities collected across turns into a single entity.
        """
        return self.combine_time_entities_from_slots(
            input.slot_tracker, output.entities
        )

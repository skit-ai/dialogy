from datetime import datetime
from typing import Any, Dict, List, Optional

from dialogy import constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.types import BaseEntity, TimeEntity


def has_time_component(entity: BaseEntity) -> bool:
    return entity.type in [
        CombineDateTimeOverSlots.TIME,
        CombineDateTimeOverSlots.DATETIME,
    ]


def is_date(entity: BaseEntity) -> bool:
    return entity.type == CombineDateTimeOverSlots.DATE


class CombineDateTimeOverSlots(Plugin):
    """
    Dialog case:

    Assume that at the moment of dialog the date is 15th December 2019.

    [1] BOT: When do you want to visit?
    [2] USER: Day after tomorrow        # entity = {'type': 'date', 'value': '2019-12-17'}
    [3] BOT: At what time?
    [4] USER: 3 pm                      # entity = {'type': 'time', 'value': '2019-12-15T15:00:00+0000'}

    We want to use the slots such that the date from interaction [2] and the time from interaction [4] are combined into a single entity.

    We receive this as a tracked slot:

    ```json
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
    ```

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
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        trigger_intents: Optional[List[str]] = None,
        debug: bool = False,
    ) -> None:
        super().__init__(
            access=access,
            mutate=mutate,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )
        self.trigger_intents = trigger_intents

    def join(self, current_entity: TimeEntity, previous_entity: TimeEntity) -> None:
        combined_value = None
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

        if not combined_value:
            return

        current_entity.value = combined_value.isoformat()
        current_entity.set_value(current_entity.value)

    def utility(self, *args: Any) -> Any:
        """
        Combine the date and time entities collected across turns into a single entity.
        """
        tracker: List[Dict[str, Any]]
        entities: List[BaseEntity]

        tracked_entity = None
        tracked_intent = None

        tracker, entities = args

        if not self.trigger_intents:
            return

        if not tracker:
            return

        for entity in entities:
            if entity.type not in CombineDateTimeOverSlots.SUPPORTED_ENTITIES:
                continue

            tracked_intents = [
                intent
                for intent in tracker
                if intent[const.NAME] in self.trigger_intents
            ]

            if not tracked_intents:
                continue

            tracked_intent = tracked_intents[0]
            tracked_slots = tracked_intent.get(const.SLOTS, [])

            if not tracked_slots:
                continue

            tracked_entities_metadata = tracked_slots[0][const.EntityKeys.VALUES]

            if not tracked_entities_metadata:
                continue

            if not isinstance(tracked_entities_metadata, list):
                continue

            tracked_entity_metadata = tracked_entities_metadata[0]
            tracked_entity_metadata[const.EntityKeys.VALUES] = [
                {const.VALUE: tracked_entity_metadata[const.VALUE]}
            ]
            tracked_entity = TimeEntity(**tracked_entity_metadata)
            self.join(entity, tracked_entity)  # type: ignore

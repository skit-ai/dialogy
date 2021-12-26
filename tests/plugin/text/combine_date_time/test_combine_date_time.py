from datetime import datetime

import pytest

from dialogy import constants as const
from dialogy.plugins import CombineDateTimeOverSlots, DucklingPlugin
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_plugin_cases(payload) -> None:
    """
    Test cases where the plugin should work.
    """
    entities = payload.get("inputs", {}).get("entities", [])
    tracker = payload.get("inputs", {}).get("tracker", [])
    expected = payload.get("expected", {})
    duckling_plugin = DucklingPlugin(
        dimensions=["date", "time"], timezone="Asia/Kolkata", access=lambda x: x
    )

    for i, entity in enumerate(entities):
        current_turn_entities = duckling_plugin._reshape(entity, i)

    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=["_callback_"],
        access=lambda w: (tracker, w.output[const.ENTITIES]),
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    workflow.output = {const.ENTITIES: current_turn_entities}
    output = workflow.run(input_=[])
    entity_values = [entity.get_value() for entity in output[const.ENTITIES]]

    if len(entity_values) != len(expected):
        pytest.fail(
            "Expected {} entities but got {}".format(len(expected), len(entity_values))
        )

    for entity_value, expected_value in zip(entity_values, expected):
        try:
            assert entity_value == datetime.fromisoformat(
                expected_value
            ), f"Expected {datetime.fromisoformat(expected_value)} but got {entity_value}"
        except (ValueError, TypeError):
            assert entity_value == expected_value


def test_plugin_exit_at_missing_trigger_intents():
    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=[], access=lambda w: ([], w.output[const.ENTITIES])
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    output = workflow.run(input_=[])
    assert output[const.ENTITIES] == []


def test_plugin_exit_at_missing_tracker():
    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=["_callback_"], access=lambda w: ([], w.output[const.ENTITIES])
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    output = workflow.run(input_=[])
    assert output[const.ENTITIES] == []

from datetime import datetime

import pytest

from dialogy import constants as const
from dialogy.base import Input, Output
from dialogy.plugins import CombineDateTimeOverSlots, DucklingPlugin
from dialogy.workflow import Workflow
from tests import load_tests


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_plugin_cases(payload) -> None:
    """
    Test cases where the plugin should work.
    """
    entities = payload.get("inputs", {}).get("entities", [])
    tracker = payload.get("inputs", {}).get("tracker", [])
    expected = payload.get("expected", {})
    duckling_plugin = DucklingPlugin(
        dimensions=["date", "time"], timezone="Asia/Kolkata", dest="output.entities"
    )

    for i, entity in enumerate(entities):
        current_turn_entities = duckling_plugin._reshape(entity, i)

    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=["_callback_"],
        dest="output.entities",
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    _, output = workflow.run(
        Input(utterances=[[{"transcript": ""}]], slot_tracker=tracker),
        Output(entities=current_turn_entities)
    )
    output = output.dict()
    entity_values = [entity["value"] for entity in output[const.ENTITIES]]

    if len(entity_values) != len(expected):
        pytest.fail(
            "Expected {} entities but got {}".format(len(expected), len(entity_values))
        )

    for entity_value, expected_value in zip(entity_values, expected):
        try:
            expected = datetime.fromisoformat(expected_value)
            generated = datetime.fromisoformat(entity_value)
            assert generated == expected, f"Expected {expected} but got {generated}"
        except (ValueError, TypeError):
            assert entity_value == expected_value


def test_plugin_exit_at_missing_trigger_intents():
    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=[], dest="output.entities"
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    _, output = workflow.run(Input(utterances=[[{"transcript": ""}]]))
    output = output.dict()
    assert output[const.ENTITIES] == []


def test_plugin_exit_at_missing_tracker():
    combine_date_time_plugin = CombineDateTimeOverSlots(
        trigger_intents=["_callback_"], dest="output.entities"
    )

    workflow = Workflow(plugins=[combine_date_time_plugin])
    _, output = workflow.run(Input(utterances=[[{"transcript": ""}]]))
    output = output.dict()
    assert output[const.ENTITIES] == []

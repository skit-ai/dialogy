import pytest

from dialogy.postprocessing.text.slot_filler.rule_slot_filler import (
    RuleBasedSlotFillerPlugin,
)
from dialogy.workflow import Workflow
from dialogy.types.entities import BaseEntity
from dialogy.types.intents import Intent


def test_rule_slot_filler():
    rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}

    def access(workflow):
        return workflow.output

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules).exec(access=access)
    workflow = Workflow(preprocessors=[], postprocessors=[slot_filler])
    intent = Intent(name="intent", score=0.8)

    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
        slot_name="basic_slot",
    )

    workflow.output = (intent, [entity])
    workflow.run("")
    assert workflow.output[0].slots["basic_slot"].values[0] == entity


def test_missing_access_fn():
    rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules).exec()
    workflow = Workflow(preprocessors=[], postprocessors=[slot_filler])
    intent = Intent(name="intent", score=0.8)

    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
        slot_name="basic_slot",
    )

    workflow.output = (intent, [entity])

    with pytest.raises(TypeError):
        workflow.run("")


def test_incorrect_access_fn():
    rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}
    access = 5

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules).exec(access=access)
    workflow = Workflow(preprocessors=[], postprocessors=[slot_filler])
    intent = Intent(name="intent", score=0.8)

    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
        slot_name="basic_slot",
    )

    workflow.output = (intent, [entity])

    with pytest.raises(TypeError):
        workflow.run("")

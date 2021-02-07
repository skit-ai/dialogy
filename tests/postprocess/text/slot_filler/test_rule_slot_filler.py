"""
[summary]

Returns:
    [type]: [description]
"""
from typing import Any
import pytest

from dialogy.postprocess.text.slot_filler.rule_slot_filler import (
    RuleBasedSlotFillerPlugin,
)
from dialogy.workflow import Workflow
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent


def test_rule_slot_filler() -> None:
    rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}

    def access(workflow: Workflow) -> Any:
        return workflow.output

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules)(access=access)
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

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules)()
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

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules)(access=access)
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
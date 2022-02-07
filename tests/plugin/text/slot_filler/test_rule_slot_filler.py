"""
This is a tutorial for understanding the use of `RuleBasedSlotFillerPlugin`.
"""
from textwrap import fill
from typing import Any

import pytest

import dialogy.constants as const
from dialogy.plugins import RuleBasedSlotFillerPlugin
from dialogy.base import Output, Input
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow

# This tutorial would be centered around these rules:
rules = {
    "intent_1": {
        "entity_1_slot": "entity_1"
        # This means, `entity_1` will reside in a slot named `entity_1_slot` for `intent_1`.
    },
    "intent_2": {
        "entity_1_slot": "entity_1",
        "entity_2_slot": "entity_2",
    },
}


def test_slot_filling() -> None:
    """
    This test case covers a trivial usage of a slot-filler.
    We have `rules` that demonstrate association of intents with entities and their respective slot-configuration.
    """
    intent_name = "intent_1"

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents")

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity])

    _, output = workflow.run(Input(utterances=body))
    intent, *_ = output[const.INTENTS]

    # `workflow.output[0]` is the `Intent` we created.
    # so we are checking if the `entity_1_slot` is filled by our mock entity.
    assert intent["slots"]["entity_1_slot"]["values"][0] == entity.json()


def test_slot_no_fill() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents")

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity])

    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # we can see that the `entity_2_slot` is not filled by our mock entity.
    assert "entity_1_slot" not in output[const.INTENTS][0]["slots"]


def test_slot_invalid_intent() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """
    intent_name = "intent_1"
    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents")

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", [1]) \
        .set("output.entities", [entity])

    with pytest.raises(AttributeError):
        workflow.run(Input(utterances=body))


def test_slot_invalid_intents() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents")

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", []) \
        .set("output.entities", [entity])
    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # we can see that the `entity_2_slot` is not filled by our mock entity.
    assert output[const.INTENTS] == []


def test_slot_dual_fill() -> None:
    """
    Let's try filling both the slots this time!
    `intent_2` supports both `entity_1` and `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_2"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents")

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # and mock `Entity`-ies.
    body = "12th december"
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0]["slots"]["entity_1_slot"]["values"] == [entity_1.json()]
    assert output[const.INTENTS][0]["slots"]["entity_2_slot"]["values"] == [entity_2.json()]


def test_slot_filling_multiple() -> None:
    """
    Let's try filling both the slots this time with fill_multiple=True!
    `intent_2` supports both `entity_1` and `entity_2`.
    """
    intent_name = "intent_2"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, dest="output.intents", fill_multiple=True
    )

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # and mock `Entity`-ies.
    body = "12th december"
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0]["slots"]["entity_1_slot"]["values"] == [entity_1.json()]
    assert output[const.INTENTS][0]["slots"]["entity_2_slot"]["values"] == [entity_2.json()]


def test_slot_competition_fill_multiple() -> None:
    """
    What happens when we have two entities of the same type but different value?
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents", fill_multiple=True)

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have two entities which compete for the same slot but have different values.
    body = "12th december"
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value_2"}],
    )

    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.

    assert output[const.INTENTS][0]["slots"]["entity_1_slot"]["values"] == [entity_1.json(), entity_2.json()]


def test_slot_competition_fill_one() -> None:
    """
    What happens when we have two entities of the same type but different value?
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, dest="output.intents", fill_multiple=False)

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have two entities which compete for the same slot but have different values.
    body = "12th december"
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="entity_1",
        values=[{"key": "value_2"}],
    )

    workflow \
        .set("output.intents", [intent]) \
        .set("output.entities", [entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body))

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.

    assert "entity_1_slot" not in output[const.INTENTS][0]["slots"]
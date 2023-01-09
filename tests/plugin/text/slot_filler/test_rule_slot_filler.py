"""
This is a tutorial for understanding the use of `RuleBasedSlotFillerPlugin`.
"""
from textwrap import fill
from typing import Any

import pytest

import dialogy.constants as const
from dialogy.base import Input, Output
from dialogy.plugins import RuleBasedSlotFillerPlugin
from dialogy.types import BaseEntity
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
    body = [[{"transcript": "12th december"}]]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    output = Output(intents=[intent], entities=[entity])
    # workflow.set("output.intents", [intent]).set("output.entities", [entity])

    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()
    intent, *_ = output[const.INTENTS]

    # `workflow.output[0]` is the `Intent` we created.
    # so we are checking if the `entity_1_slot` is filled by our mock entity.
    assert intent["slots"][0]["values"][0] == entity.dict()


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
    body = [[{"transcript": "12th december"}]]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_2",
        values=[{"value": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    output = Output(intents=[intent], entities=[entity])
    # workflow.set("output.intents", [intent]).set("output.entities", [entity])

    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    # `workflow.output[0]` is the `Intent` we created.
    # we can see that the `entity_2_slot` is not filled by our mock entity.
    assert len(output[const.INTENTS][0]["slots"]) == 0


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
    body = [[{"transcript": "12th december"}]]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    output = Output(intents=[], entities=[entity])
    # workflow.set("output.intents", []).set("output.entities", [entity])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

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
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_2",
        values=[{"value": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    # workflow.set("output.intents", [intent]).set(
    #     "output.entities", [entity_1, entity_2]
    # )
    output = Output(intents=[intent], entities=[entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0]["slots"][0]["values"] == [entity_1.dict()]
    assert output[const.INTENTS][0]["slots"][1]["values"] == [entity_2.dict()]


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
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_2",
        values=[{"value": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    # workflow.set("output.intents", [intent]).set(
    #     "output.entities", [entity_1, entity_2]
    # )
    output = Output(intents=[intent], entities=[entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0]["slots"][0]["values"] == [entity_1.dict()]
    assert output[const.INTENTS][0]["slots"][1]["values"] == [entity_2.dict()]


def test_slot_competition_fill_multiple() -> None:
    """
    What happens when we have two entities of the same type but different value?
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, dest="output.intents", fill_multiple=True
    )

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have two entities which compete for the same slot but have different values.
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value_2"}],
    )

    # workflow.set("output.intents", [intent]).set(
    #     "output.entities", [entity_1, entity_2]
    # )
    output = Output(intents=[intent], entities=[entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.

    assert output[const.INTENTS][0]["slots"][0]["values"] == [
        entity_1.dict(),
        entity_2.dict(),
    ]


def test_slot_competition_fill_one() -> None:
    """
    What happens when we have two entities of the same type but different value?
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, dest="output.intents", fill_multiple=False
    )

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have two entities which compete for the same slot but have different values.
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        entity_type="entity_1",
        values=[{"value": "value_2"}],
    )

    output = Output(intents=[intent], entities=[entity_1, entity_2])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    # `workflow.output[0]` is the `Intent` we created.
    # Slots should be empty since it should discard conflicting
    # value unless fill_multiple is set to True

    assert "entity_1_slot" not in output[const.INTENTS][0]["slots"]

def test_slot_filling_order() -> None:
    """
    Here, we will see that entities of same type filled in a slot are sorted by their score in descending order.
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, dest="output.intents", fill_multiple=True
    )

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have three entities which have different scores.
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.2,
        entity_type="entity_1",
        values=[{"value": "value_1"}],
        alternative_index=2
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.9,
        entity_type="entity_1",
        values=[{"value": "value_2"}],
        alternative_index=1
    )

    entity_3 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.5,
        entity_type="entity_1",
        values=[{"value": "value_3"}],
        alternative_index=0
    )

    # workflow.set("output.intents", [intent]).set(
    #     "output.entities", [entity_1, entity_2, entity_3], sort_output_attributes=False
    # )  # we don't want to sort the output attributes here as we want to test if slot.json() does the sorting for us.
    output = Output(intents=[intent], entities=[entity_1, entity_2, entity_3])
    _, output = workflow.run(Input(utterances=body), output)
    output = output.dict()

    slot_values = output["intents"][0]["slots"][0]["values"]
    assert all(
        slot_values[i]["score"] >= slot_values[i + 1]["score"]
        for i in range(len(slot_values) - 1)
    )


def test_slot_filling_with_expected_slots() -> None:
    """
    Here, we will see that entities of same type filled in a slot are sorted by their score in descending order.
    Only if the slots are expected.
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

    # Here we have three entities which have different scores.
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.2,
        entity_type="entity_1",
        values=[{"value": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.9,
        entity_type="entity_2",
        values=[{"value": "value_2"}],
    )

    entity_3 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.5,
        entity_type="entity_1",
        values=[{"value": "value_3"}],
    )

    output = Output(intents=[intent], entities=[entity_1, entity_2, entity_3])
    _, output = workflow.run(
        Input(utterances=body, expected_slots=["entity_1_slot"]), output
    )
    output = output.dict()

    assert [s["name"]
            for s in output["intents"][0]["slots"]] == ["entity_1_slot"]


def test_slot_filling_order_by_alternative_index() -> None:
    """
    Here, we will see that entities of same type filled in a slot are sorted by their alternative_index in ascending order.
    """
    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, dest="output.intents", fill_multiple=True, sort_by_score=False
    )

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # ... a mock `Intent`
    intent = Intent(name=intent_name, score=0.8)

    # Here we have three entities which have different scores.
    body = [[{"transcript": "12th december"}]]
    entity_1 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.2,
        entity_type="entity_1",
        values=[{"value": "value_1"}],
        alternative_index=2
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.9,
        entity_type="entity_1",
        values=[{"value": "value_2"}],
        alternative_index=1
    )

    entity_3 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body[0][0]["transcript"],
        dim="default",
        score=0.5,
        entity_type="entity_1",
        values=[{"value": "value_3"}],
        alternative_index=0
    )

    output = Output(intents=[intent], entities=[entity_1, entity_2, entity_3])

    _, output = workflow.run(Input(utterances=body), output)
    slot_values = output.dict()["intents"][0]["slots"][0]["values"]
    assert all(
        slot_values[i]["alternative_index"] <= slot_values[i +
                                                           1]["alternative_index"]
        for i in range(len(slot_values) - 1)
    )

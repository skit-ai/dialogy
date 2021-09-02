"""
This is a tutorial for understanding the use of `RuleBasedSlotFillerPlugin`.
"""
from typing import Any

import pytest

import dialogy.constants as const
from dialogy.plugins import RuleBasedSlotFillerPlugin
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

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

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
        type="entity_1",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # so we are checking if the `entity_1_slot` is filled by our mock entity.
    assert output[const.INTENTS][0].slots["entity_1_slot"].values[0] == entity


def test_slot_no_fill() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

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
        type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # we can see that the `entity_2_slot` is not filled by our mock entity.
    assert "entity_1_slot" not in output[const.INTENTS][0].slots


def test_slot_invalid_intent() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [1], const.ENTITIES: [entity]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # we can see that the `entity_2_slot` is not filled by our mock entity.
    assert output[const.INTENTS] == [1]


def test_slot_invalid_intents() -> None:
    """
    Here, we will see that an entity will not fill an intent unless the intent has a slot for it.
    `intent_1` doesn't have a slot for an entity of type `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

    # Create a mock `workflow`
    workflow = Workflow([slot_filler])

    # and a mock `Entity`.
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [], const.ENTITIES: [entity]}
    output = workflow.run(body)

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
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

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
        type="entity_1",
        values=[{"key": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity_1, entity_2]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0].slots["entity_1_slot"].values == [entity_1]
    assert output[const.INTENTS][0].slots["entity_2_slot"].values == [entity_2]


def test_slot_filling_multiple() -> None:
    """
    Let's try filling both the slots this time with fill_multiple=True!
    `intent_2` supports both `entity_1` and `entity_2`.
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_2"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(
        rules=rules, access=access, fill_multiple=True
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
        type="entity_1",
        values=[{"key": "value"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="entity_2",
        values=[{"key": "value"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity_1, entity_2]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert output[const.INTENTS][0].slots["entity_1_slot"].values == [entity_1]
    assert output[const.INTENTS][0].slots["entity_2_slot"].values == [entity_2]


def test_slot_competition() -> None:
    """
    What happens when we have two entities of the same type but different value?
    """

    def access(workflow: Workflow) -> Any:
        return (workflow.output[const.INTENTS], workflow.output[const.ENTITIES])

    intent_name = "intent_1"

    # Setting up the slot-filler, both instantiation and plugin is created. (notice two calls).
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)

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
        type="entity_1",
        values=[{"key": "value_1"}],
    )

    entity_2 = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="entity_1",
        values=[{"key": "value_2"}],
    )

    # The RuleBasedSlotFillerPlugin specifies that it expects `Tuple[Intent, List[Entity])` on `access(workflow)`.
    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity_1, entity_2]}
    output = workflow.run(body)

    # `workflow.output[0]` is the `Intent` we created.
    # The `entity_1_slot` and `entity_2_slot` are filled.
    assert "entity_1_slot" not in output[const.INTENTS][0].slots


def test_incorrect_access_fn() -> None:
    """
    This test shows that the plugin needs `access` function to be a `PluginFn`,
    or else it throws a `TypeError`.
    """
    rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}
    access = 5

    slot_filler = RuleBasedSlotFillerPlugin(rules=rules, access=access)
    workflow = Workflow([slot_filler])
    intent = Intent(name="intent", score=0.8)

    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
    )

    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity]}

    with pytest.raises(TypeError):
        workflow.run("")


def test_missing_access_fn() -> None:
    """
    This test shows that the plugin needs an `access` provided or else it raises a type error.
    """
    slot_filler = RuleBasedSlotFillerPlugin(rules=rules)
    workflow = Workflow([slot_filler])
    intent = Intent(name="intent", score=0.8)

    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
    )

    workflow.output = {const.INTENTS: [intent], const.ENTITIES: [entity]}

    with pytest.raises(TypeError):
        workflow.run("")

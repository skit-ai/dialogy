"""
Tests for intents
"""
import pytest

from dialogy.types import BaseEntity
from dialogy.types.intent import Intent


class MockPlugin:
    ...


def test_intent_parser() -> None:
    """
    Creating an instance.
    """
    intent = Intent(name="intent_name", score=0.5)
    intent.add_parser(MockPlugin())

    assert intent.parsers == ["MockPlugin"]


def test_rule_application() -> None:
    """
    A rule application case.

    This is helpful if you wish to understand how slots are filled within an intent.
    An initial setup is rule application, once that's done, you can expect
    the slots to be ready for containing entities.
    """

    rules = {
        "intent": {
            "date_slot": "date",
            "number_slot": "number",
        }
    }

    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)

    assert "date_slot" in intent.slots, "date_slot should be present."
    assert "number_slot" in intent.slots, "number_slot should be present."

    assert intent.slots["date_slot"].types == ["date"]
    assert intent.slots["number_slot"].types == ["number"]


def test_missing_rule() -> None:
    """
    In case there is no rule for an intent?
    """
    rules = {
        "intent": {
            "date_slot": "date",
            "number_slot": "number",
        }
    }

    intent = Intent(name="some-other-intent", score=0.8)
    intent.apply(rules)

    assert "date_slot" not in intent.slots, "date_slot should be present."
    assert "number_slot" not in intent.slots, "number_slot should be present."


def test_slot_filling() -> None:
    """
    This test shows rule application, and filling an entity within a slot.
    """
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="basic",
        values=[{"value": "value"}],
    )
    rules = {"intent": {"basic_slot": "basic"}}
    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)

    intent.fill_slot(entity)

    assert intent.slots["basic_slot"].values[0] == entity


def test_intent_json() -> None:
    name = "intent_name"
    intent = Intent(name=name, score=0.5)
    intent_json = intent.dict()
    assert intent_json.get("name") == name


def test_rule_with_multiple_types() -> None:
    ordinal_entity = BaseEntity(
        range={"from": 0, "to": 15},
        body="12th december",
        dim="default",
        entity_type="ordinal",
        values=[{"value": "12th"}],
    )
    number_entity = BaseEntity(
        range={"from": 0, "to": 15},
        body="12 december",
        dim="default",
        entity_type="number",
        values=[{"value": "12"}],
    )
    rules = {"intent": {"basic_slot": ["ordinal", "number"]}}
    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)
    intent.fill_slot(number_entity, fill_multiple=True)
    intent.fill_slot(ordinal_entity, fill_multiple=True)

    assert intent.slots["basic_slot"].values[0] == number_entity
    assert intent.slots["basic_slot"].values[1] == ordinal_entity


def test_invalid_rule() -> None:
    rules = {"intent": {"basic_slot": [12]}}
    intent = Intent(name="intent", score=0.8)

    with pytest.raises(TypeError):
        intent.apply(rules)

"""
Tests for intents
"""

from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow


def mock_plugin(_: Workflow) -> None:
    pass


def test_intent_parser() -> None:
    """
    Creating an instance.
    """
    intent = Intent(name="intent_name", score=0.5)
    intent.add_parser(mock_plugin)

    assert intent.parsers == ["mock_plugin"]


def test_rule_application() -> None:
    """
    A rule application case.

    This is helpful if you wish to understand how slots are filled within an intent.
    An initial setup is rule application, once that's done, you can expect
    the slots to be ready for containing entities.
    """

    rules = {
        "intent": {
            "date": {"slot_name": "date_slot", "entity_type": "date"},
            "number": {"slot_name": "number_slot", "entity_type": "number"},
        }
    }

    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)

    assert "date_slot" in intent.slots, "date_slot should be present."
    assert "number_slot" in intent.slots, "number_slot should be present."

    assert intent.slots["date_slot"].type == ["date"]
    assert intent.slots["number_slot"].type == ["number"]


def test_missing_rule() -> None:
    """
    In case there is no rule for an intent?
    """
    rules = {
        "intent": {
            "date": {"slot_name": "date_slot", "entity_type": "date"},
            "number": {"slot_name": "number_slot", "entity_type": "number"},
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
        type="basic",
        values=[{"key": "value"}],
        slot_names=["basic_slot"],
    )
    rules = {"intent": {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}}
    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)

    intent.fill_slot(entity)

    assert intent.slots["basic_slot"].values[0] == entity

"""
Tests for intents
"""

from dialogy.types.intent import Intent
from dialogy.types.entity import BaseEntity
from dialogy.workflow import Workflow


def mock_plugin(_: Workflow) -> None:
    pass


def test_intent_parser():
    intent = Intent(name="intent_name", score=0.5)
    intent.add_parser(mock_plugin)

    assert intent.parsers == ["mock_plugin"]


def test_rule_application():
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


def test_slot_filling():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
        slot_name="basic_slot",
    )
    rules = {"intent": {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}}
    intent = Intent(name="intent", score=0.8)
    intent.apply(rules)

    intent.fill_slot(entity)

    assert intent.slots["basic_slot"].values[0] == entity

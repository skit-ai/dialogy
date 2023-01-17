from datetime import datetime

import pytest
import json

from dialogy.base import Input, Output
from dialogy.workflow import Workflow
from dialogy.types import Intent
from dialogy.types.entity.deserialize import EntityDeserializer
from dialogy.plugins.text.error_recovery.error_recovery import (
    Rule,
    Environment,
    ErrorRecoveryPlugin,
)
from tests import load_tests


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_error_recovery(payload):
    rules = payload.get("rules")
    let = payload.get("let")
    intents = [
        Intent(name=intent["name"], score=intent["score"])
        for intent in payload.get("intents", [])
    ]
    entities = [
        EntityDeserializer.deserialize_duckling(entity, 0)
        for entity in payload.get("entities", [])
    ]
    entities = [
        EntityDeserializer.deserialize_json(**json.loads(json.dumps(entity.dict())))
        for entity in entities
    ]

    expected_intent = payload.get("expect", {}).get("intent")
    expected_entities = payload.get("expect", {}).get("entities", [])

    if expected_intent:
        expected_intent = Intent(
            name=expected_intent["name"], score=expected_intent["score"]
        )

    let_bindings = payload.get("let")
    env = Environment(
        intents=intents,
        entities=entities,
        previous_intent=payload.get("previous_intent"),
        current_state=payload.get("current_state"),
        expected_slots=payload.get("expected_slots", set()),
    )
    rules = Rule.from_list(rules)
    env = Environment(
        intents=intents or [],
        entities=entities or [],
        previous_intent=payload.get("previous_intent"),
        current_state=payload.get("current_state"),
        expected_slots=payload.get("expected_slots", set()),
    )

    for rule in rules:
        rule.parse(env)
    entities_json = [e.dict() for e in env.entities]
    if expected_intent:
        assert env.intents[0] == expected_intent
    if expected_entities:
        assert entities_json == expected_entities


def test_error_recovery_plugin():
    rules = [
        {
            "find": "entities",
            "where": [
                {"entity.grain": "week"},
                {"entity.entity_type": {"in": ["date", "time", "datetime"]}},
                {"predicted_intent": "future_date"},
            ],
            "update": {"entity.day": ":last_day_of_week"},
        }
    ]
    workflow = Workflow([ErrorRecoveryPlugin(rules=rules)])

    entities = [
        {
            "body": "this week",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2022-07-18T00:00:00.000+00:00",
                        "grain": "week",
                        "type": "value",
                    }
                ],
                "value": "2022-07-18T00:00:00.000+00:00",
                "grain": "week",
                "type": "value",
            },
            "end": 9,
            "dim": "time",
            "latent": False,
        }
    ]

    entities = [
        EntityDeserializer.deserialize_duckling(entity, 0)
        for entity in entities
    ]
    entities = [
        EntityDeserializer.deserialize_json(**json.loads(json.dumps(entity.dict())))
        for entity in entities
    ]

    output = Output(
        intents=[Intent(name="future_date", score=0.99)],
        entities=entities,
    )
    _, output = workflow.run(
        Input(utterances=[[{"transcript": "this week"}]]), output=output
    )
    output = output.dict()
    assert output["entities"][0]["value"] == "2022-07-24T00:00:00+00:00"

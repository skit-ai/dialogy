import json

import pandas as pd
import pydash as py_
import pytest
from torch import threshold

from dialogy.base.entity_extractor import EntityScoringMixin
from dialogy.plugins import DucklingPlugin
from dialogy.types import KeywordEntity
from tests import EXCEPTIONS, load_tests


def make_entity_object(entity_items):
    duckling_plugin = DucklingPlugin(
        dest="output.entities",
        dimensions=["date", "time", "duration", "number", "people"],
        timezone="Asia/Kolkata",
        debug=False,
        locale="en_IN",
    )
    return py_.flatten(
        [
            duckling_plugin._reshape(entities, i)
            for i, entities in enumerate(entity_items)
        ]
    )


def test_remove_low_scoring_entities():
    entity_extractor = EntityScoringMixin()
    entity_extractor.threshold = 0.5
    body = "test"
    entities = [
        KeywordEntity(
            body=body,
            value=body,
            range={
                "start": 0,
                "end": len(body),
            },
            entity_type=body,
        )
    ]
    assert entity_extractor.remove_low_scoring_entities(entities) == entities


@pytest.mark.parametrize("payload", load_tests("entity_extractor", __file__))
def test_entity_extractor_for_thresholding(payload) -> None:
    """
    We test threshold on entity extractors.

    :param payload: Test case body.
    :type payload: Dict[str, Any]
    """
    entity_extractor = EntityScoringMixin()
    entity_extractor.threshold = payload["threshold"]
    input_size = payload["input_size"]
    expected = payload["expected"]

    entities = make_entity_object(payload["mock_entities"])
    entities = [
        entity.json()
        for entity in entity_extractor.entity_consensus(entities, input_size)
    ]

    for expected_entity, extracted_entity in zip(expected, entities):
        assert expected_entity["type"] == extracted_entity["type"]
        assert expected_entity["value"] == extracted_entity["value"]
        assert expected_entity["range"] == extracted_entity["range"]
        assert expected_entity["entity_type"] == extracted_entity["entity_type"]

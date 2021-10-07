import json

import pandas as pd
import pydash as py_
import pytest

from dialogy.base.entity_extractor import EntityScoringMixin
from dialogy.plugins import DucklingPlugin
from dialogy.types import KeywordEntity
from tests import EXCEPTIONS, load_tests


def make_entity_object(entity_items):
    reference_time = 1622640071000

    def access(workflow):
        return workflow.input, reference_time, "en_IN"

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    duckling_plugin = DucklingPlugin(
        access=access,
        mutate=mutate,
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
    assert expected == entities

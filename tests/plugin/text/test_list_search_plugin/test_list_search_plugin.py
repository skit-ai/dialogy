import pandas as pd
import pytest

from dialogy.plugins import ListSearchPlugin
from dialogy.base import Input, Output
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests


class EntMocker:
    def __init__(self, token, label):
        self.text = token
        self.label_ = label

    def __call__(self, transcript):
        index = self.transcripts.index(transcript)
        self.ents = (
            EntMocker(ent["value"], ent["type"]) for ent in self.all_ents[index]
        )
        return self


def test_not_supported_lang():
    with pytest.raises(ValueError):
        l = ListSearchPlugin(
            dest="output.entities",
            fuzzy_threshold=0.3,
            fuzzy_dp_config={"te": {"channel": {"hello": "hello"}}},
        )
        l.get_entities(["........."], "te")


def test_entity_not_found():
    l = ListSearchPlugin(
        dest="output.entities",
        fuzzy_threshold=0.4,
        fuzzy_dp_config={"en": {"location": {"delhi": "Delhi"}}},
    )
    assert l.get_entities(["I live in punjab"], "en") == []


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_get_list_entities(payload):
    input_ = payload.get("input")
    lang_ = payload.get("lang")
    expected = payload.get("expected")
    exception = payload.get("exception")
    config = payload.get("config")
    transcripts = [expectation["text"] for expectation in input_]

    if expected:
        list_entity_plugin = ListSearchPlugin(
            dest="output.entities",
            **config
        )

        workflow = Workflow([list_entity_plugin])
        _, output = workflow.run(Input(utterances=transcripts, lang=lang_))
        entities = output["entities"]

        if not entities and expected:
            pytest.fail("No entities found!")

        for i, entity in enumerate(entities):
            assert entity["value"] == expected[i]["value"]
            assert entity["type"] == expected[i]["type"]
            if "score" in expected[i]:
                assert entity["score"] == expected[i]["score"]
    else:
        with pytest.raises(EXCEPTIONS.get(exception)):
            list_entity_plugin = ListSearchPlugin(
                dest="output.entities", **config
            )

            workflow = Workflow([list_entity_plugin])
            workflow.run(Input(utterances=transcripts, lang=lang_))

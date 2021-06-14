from typing import Dict, List, Optional

import attr
import pytest

from dialogy.preprocess.text.list_entity_plugin import ListEntityPlugin
from dialogy.types.entity import BaseEntity
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests


@attr.s
class MockCustomEntity(BaseEntity):
    """
    Extend BaseEntity for products of any kind.
    An instance of this class should be used to
    wrap tokens that are understood as product entities.
    """

    values = attr.ib(
        type=List[Dict[str, str]],
        default=attr.Factory(list),
        validator=attr.validators.instance_of(List),
    )
    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
    value: Optional[str] = attr.ib(default=None)

    def __attrs_post_init__(self) -> None:
        self.entity_type = "mock_entity"

    def set_value(self, keyword: Optional[str] = None):
        if keyword:
            value = keyword.lower().strip()
            self.values = [{"value": value}]
            self.value = value
        else:
            self.value = self.values[0]["value"]


class EntMocker:
    def __init__(self, token, label):
        self.text = token
        self.label_ = label


class SpacyMocker:
    def __init__(self, payload):
        self.transcripts = [expectation["text"] for expectation in payload]
        self.all_ents = [expectation["entities"] for expectation in payload]
        self.ents = None

    def __call__(self, transcript):
        index = self.transcripts.index(transcript)
        self.ents = (
            EntMocker(ent["value"], ent["type"]) for ent in self.all_ents[index]
        )
        return self


def mutate(w, v):
    w.output = v


def test_value_error_if_incorrect_style():
    with pytest.raises(ValueError):
        l = ListEntityPlugin(
            access=lambda w: (w.input,), mutate=mutate, style="unknown", entity_map={}
        )
        l._parse({"location": ["..."]})


def test_value_error_if_spacy_missing():
    with pytest.raises(ValueError):
        l = ListEntityPlugin(
            access=lambda w: (w.input,),
            mutate=mutate,
            style="spacy",
            entity_map={},
            spacy_nlp=None,
        )
        l.ner_search("...")


def test_type_error_if_compiled_patterns_missing():
    with pytest.raises(TypeError):
        l = ListEntityPlugin(
            access=lambda w: (w.input,),
            mutate=mutate,
            style="spacy",
            entity_map={},
            spacy_nlp=None,
        )
        l.regex_search("...")


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_get_list_entities(payload):
    input_ = payload.get("input")
    expected = payload.get("expected")
    exception = payload.get("exception")
    config = payload.get("config")
    spacy_mocker = None
    transcripts = [expectation["text"] for expectation in input_]
    entity_class_map = {"MockCustomEntity": MockCustomEntity}

    for entity_type, entity_class_name in config["entity_map"].items():
        config["entity_map"][entity_type] = entity_class_map[entity_class_name]

    if config["style"] == "spacy":
        spacy_mocker = SpacyMocker(input_)

    if expected:
        list_entity_plugin = ListEntityPlugin(
            access=lambda w: (w.input,), mutate=mutate, spacy_nlp=spacy_mocker, **config
        )()

        workflow = Workflow(preprocessors=[list_entity_plugin], postprocessors=[])
        workflow.run(input_=transcripts)
        entities = workflow.output

        if not entities and expected:
            pytest.fail("No entities found!")

        for i, entity in enumerate(entities):
            assert entity.value == expected[i]["value"]
            assert entity.type == expected[i]["type"]
    else:
        with pytest.raises(EXCEPTIONS.get(exception)):
            list_entity_plugin = ListEntityPlugin(
                access=lambda w: (w.input,),
                mutate=mutate,
                spacy_nlp=spacy_mocker,
                **config
            )()

            workflow = Workflow(preprocessors=[list_entity_plugin], postprocessors=[])
            workflow.run(input_=input_)

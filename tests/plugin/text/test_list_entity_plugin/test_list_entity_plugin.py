import pandas as pd
import pytest

from dialogy.base import Input, Output
from dialogy.plugins import ListEntityPlugin
from dialogy.types import KeywordEntity
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests


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
        l = ListEntityPlugin(dest="output.entities", style="unknown")
        l._parse({"location": ["..."]})


def test_value_error_if_spacy_missing():
    with pytest.raises(ValueError):
        l = ListEntityPlugin(
            dest="output.entities",
            style="spacy",
            spacy_nlp=None,
        )
        l.ner_search("...")


def test_type_error_if_compiled_patterns_missing():
    with pytest.raises(TypeError):
        l = ListEntityPlugin(
            dest="output.entities",
            style="spacy",
            spacy_nlp=None,
        )
        l.regex_search("...")


def test_entity_extractor_transform():
    entity_extractor = ListEntityPlugin(
        dest="output.entities",
        input_column="data",
        output_column="entities",
        use_transform=True,
        style="regex",
        candidates={"fruits": {"apple": [r"apples?"], "orange": [r"oranges?"]}},
    )
    df = pd.DataFrame(
        [
            {
                "data": '["lets have apples today"]',
            },
            {
                "data": '[[{"transcript": "lets have oranges today"}]]',
                "entities": [
                    KeywordEntity(
                        range={"start": 0, "end": 0},
                        value="apple",
                        type="fruits",
                        body="apple",
                    )
                ],
            },
        ],
        columns=["data", "entities"],
    )
    df_ = entity_extractor.transform(df)
    parsed_entities = df_.entities
    assert parsed_entities.iloc[0][0].entity_type == "fruits"
    assert parsed_entities.iloc[0][0].value == "apple"
    assert parsed_entities.iloc[1][1].entity_type == "fruits"
    assert parsed_entities.iloc[1][1].value == "orange"


def test_entity_extractor_no_transform():
    entity_extractor = ListEntityPlugin(
        dest="output.entities",
        input_column="data",
        output_column="entities",
        use_transform=False,
        style="regex",
        candidates={"fruits": {"apple": [r"apples?"], "orange": [r"oranges?"]}},
    )
    df = pd.DataFrame(
        [
            {
                "data": '["lets have apples today"]',
            },
            {
                "data": '[[{"transcript": "lets have oranges today"}]]',
                "entities": [
                    KeywordEntity(
                        range={"start": 0, "end": 0},
                        value="apple",
                        type="fruits",
                        body="apple",
                    )
                ],
            },
        ],
        columns=["data", "entities"],
    )
    df_ = entity_extractor.transform(df)
    parsed_entities = df_.entities
    assert pd.isna(parsed_entities.iloc[0]) is True


def test_entity_extractor_transform_no_existing_entity():
    entity_extractor = ListEntityPlugin(
        dest="output.entities",
        input_column="data",
        output_column="entities",
        use_transform=True,
        style="regex",
        candidates={"fruits": {"apple": [r"apples?"], "orange": [r"oranges?"]}},
    )
    df = pd.DataFrame(
        [
            {
                "data": '["lets have apples today"]',
            },
            {
                "data": [[{"transcript": "lets have oranges today"}]],
            },
        ]
    )
    df_ = entity_extractor.transform(df)
    parsed_entities = df_.entities
    assert parsed_entities.iloc[0][0].entity_type == "fruits"
    assert parsed_entities.iloc[0][0].value == "apple"
    assert parsed_entities.iloc[1][0].entity_type == "fruits"
    assert parsed_entities.iloc[1][0].value == "orange"


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_get_list_entities(payload):
    input_ = payload.get("input")
    expected = payload.get("expected")
    exception = payload.get("exception")
    config = payload.get("config")
    spacy_mocker = None
    transcripts = [expectation["text"] for expectation in input_]

    if config["style"] == "spacy":
        spacy_mocker = SpacyMocker(input_)

    if expected:
        list_entity_plugin = ListEntityPlugin(
            dest="output.entities", spacy_nlp=spacy_mocker, **config
        )

        workflow = Workflow([list_entity_plugin])
        _, output = workflow.run(input_=Input(utterances=transcripts))
        entities = output["entities"]

        if not entities and expected:
            pytest.fail("No entities found!")

        for i, entity in enumerate(entities):
            assert entity["value"] == expected[i]["value"]
            assert entity["entity_type"] == expected[i]["entity_type"]
            if "score" in expected[i]:
                assert entity["score"] == expected[i]["score"]
    else:
        with pytest.raises(EXCEPTIONS.get(exception)):
            list_entity_plugin = ListEntityPlugin(
                dest="output.entities", spacy_nlp=spacy_mocker, **config
            )

            workflow = Workflow([list_entity_plugin])
            _, output = workflow.run(input_=Input(utterances=transcripts))

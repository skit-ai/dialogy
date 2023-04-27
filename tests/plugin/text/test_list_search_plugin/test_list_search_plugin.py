import json

import pytest
import os
import hashlib
import pathlib

from dialogy.base import Input
from dialogy.plugins.registry import ListSearchPlugin
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


class MockDocument:
    def __init__(self, d) -> None:
        self.d = d

    def to_dict(self):
        return self.d


def test_get_words_from_nlp(mocker):
    mocker.patch("stanza.download", return_value=1)
    mocker.patch("stanza.Pipeline", return_value={})
    l = ListSearchPlugin(
        dest="output.entities",
        fuzzy_threshold=0.3,
        fuzzy_dp_config={
            "en": {
                "location": {
                    "New Delhi": "Delhi",
                    "new deli": "Delhi",
                    "delhi": "Delhi",
                }
            }
        },
    )
    expected = json.loads(
        """[[{"id": 1, "text": "I", "lemma": "I", "upos": "PRON", "xpos": "PRP", 
    "feats": "Case=Nom|Number=Sing|Person=1|PronType=Prs", "head": 2, "deprel": "nsubj", "misc": "", 
    "start_char": 0, "end_char": 1, "ner": "O"}, {"id": 2, "text": "live", "lemma": "live", 
    "upos": "VERB", "xpos": "VBP", "feats": "Mood=Ind|Tense=Pres|VerbForm=Fin", "head": 0, "deprel": "root", 
    "misc": "", "start_char": 2, "end_char": 6, "ner": "O"}, {"id": 3, "text": "in", "lemma": "in", 
    "upos": "ADP", "xpos": "IN", "head": 4, "deprel": "case", "misc": "", "start_char": 7, "end_char": 9, 
    "ner": "O"}, {"id": 4, "text": "punjab", "lemma": "punjab", "upos": "PROPN", 
    "xpos": "NNP", "feats": "Number=Sing", "head": 2, "deprel": "obl", "misc": "", 
    "start_char": 10, "end_char": 16, "ner": "O"}]]"""
    )

    def mock_nlp(query):
        return MockDocument(expected)

    assert expected[0] == l.get_words_from_nlp(mock_nlp, "I live in punjab")


def test_not_supported_lang(mocker):
    mocker.patch("stanza.download", return_value=1)
    mocker.patch("stanza.Pipeline", return_value={})
    with pytest.raises(ValueError):
        l = ListSearchPlugin(
            dest="output.entities",
            fuzzy_threshold=0.3,
            fuzzy_dp_config={"te": {"channel": {"hello": "hello"}}},
        )
        l.get_entities(["........."], "te")


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_get_list_entities(payload, mocker):
    input_ = payload.get("input")
    lang_ = payload.get("lang")
    expected = payload.get("expected")
    config = payload.get("config")
    nlp_words = payload.get("nlp_words")
    transcripts = [[{"transcript": expectation["text"]} for expectation in input_]]

    mocker.patch("stanza.download", return_value=1)
    mocker.patch("stanza.Pipeline", return_value={})
    mocker.patch(
        "dialogy.plugins.ListSearchPlugin.get_words_from_nlp", return_value=nlp_words
    )

    list_entity_plugin = ListSearchPlugin(dest="output.entities", **config)

    workflow = Workflow([list_entity_plugin])
    _, output = workflow.run(Input(utterances=transcripts, lang=lang_))
    output = output.dict()
    entities = output["entities"]

    if not entities and expected:
        pytest.fail("No entities found!")

    for i, entity in enumerate(entities):
        assert entity["value"] == expected[i]["value"]
        assert entity["type"] == expected[i]["type"]
        if "score" in expected[i]:
            assert entity["score"] == expected[i]["score"]


def test_nlp_download_method():
    download_default_path = os.path.join(os.path.expanduser("~"), "stanza_resources")

    if os.path.exists(download_default_path):
        os.remove(download_default_path)

    # first check if model can be downloaded
    l = ListSearchPlugin(
        dest="output.entities",
        fuzzy_threshold=0.3,
        fuzzy_dp_config={
            "en": {
                "location": {
                    "New Delhi": "Delhi",
                    "new deli": "Delhi",
                    "delhi": "Delhi",
                }
            }
        },
    )

    assert os.path.exists(download_default_path)

    # now check if model is reused and not downloaded again
    # compute the checksum of resources file in download path
    original_checksum = hashlib.md5(
        pathlib.Path(
            os.path.join(f"{download_default_path}/resources.json")
        ).read_bytes()
    ).hexdigest()

    del l

    l = ListSearchPlugin(
        dest="output.entities",
        fuzzy_threshold=0.3,
        fuzzy_dp_config={
            "en": {
                "location": {
                    "New Delhi": "Delhi",
                    "new deli": "Delhi",
                    "delhi": "Delhi",
                }
            }
        },
    )

    new_checksum = hashlib.md5(
        pathlib.Path(
            os.path.join(f"{download_default_path}/resources.json")
        ).read_bytes()
    ).hexdigest()

    assert new_checksum == original_checksum

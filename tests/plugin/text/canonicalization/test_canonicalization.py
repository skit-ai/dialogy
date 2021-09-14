import pandas as pd

from dialogy.plugins.text.canonicalization import CanonicalizationPlugin
from dialogy.plugins.text.list_entity_plugin import ListEntityPlugin
from dialogy.types import KeywordEntity
from dialogy.workflow import Workflow


def canon_access(w):
    return w.output["entities"], w.input["classification_input"]


def canon_mutate(w, v):
    w.output["classification_input"] = v


canonicalization = CanonicalizationPlugin(
    mask_tokens=["hello"],
    input_column="data",
    access=canon_access,
    mutate=canon_mutate,
)


def entity_access(w):
    return (w.input["ner_input"],)


def entity_mutate(w, v):
    w.output["entities"] = v


list_entity_plugin = ListEntityPlugin(
    candidates={"fruits": {"apple": ["apple", "apples"]}},
    style="regex",
    access=entity_access,
    mutate=entity_mutate,
    threshold=0,
)

workflow = Workflow([list_entity_plugin, canonicalization])


def test_canonicalization_utility():
    output = workflow.run(
        input_={"classification_input": ["hello apple"], "ner_input": ["hello apple"]}
    )
    assert output["classification_input"] == ["MASK fruits"]


def test_canonicalization_transform():
    df = pd.DataFrame(
        [
            {
                "data": ["hello apple"],
                "entities": [
                    KeywordEntity(
                        type="fruits",
                        body="apple",
                        parsers=["ListEntityPlugin"],
                        score=1.0,
                        alternative_index=0,
                        value="apple",
                        range={"start": 6, "end": 11},
                    )
                ],
            },
            {
                "data": ["hello apple"],
                "entities": [{}],
            },
        ]
    )
    df = canonicalization.transform(df)
    assert df["data"][0] == ["MASK fruits"]

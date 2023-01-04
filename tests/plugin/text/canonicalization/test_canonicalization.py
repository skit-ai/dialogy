import json

import pandas as pd

from dialogy.base import Input
from dialogy.plugins.text.canonicalization import CanonicalizationPlugin
from dialogy.plugins.text.list_entity_plugin import ListEntityPlugin
from dialogy.types import KeywordEntity
from dialogy.workflow import Workflow

canonicalization = CanonicalizationPlugin(
    mask_tokens=["hello"],
    input_column="data",
    use_transform=True,
    threshold=0.1,
    debug=False,
    dest="input.clf_feature",
)


no_op_canonicalization = CanonicalizationPlugin(
    mask_tokens=["hello"],
    input_column="data",
    threshold=0.1,
    dest="input.clf_feature",
    debug=False,
    use_transform=False,
)


list_entity_plugin = ListEntityPlugin(
    candidates={"fruits": {"apple": ["apple", "apples"]}},
    style="regex",
    dest="output.entities",
    debug=False,
)

workflow = Workflow([list_entity_plugin, canonicalization])

TEST_DATA = pd.DataFrame(
    [
        {
            "data": json.dumps(["hello apple", "hello orange"]),
            "entities": [
                KeywordEntity(
                    entity_type="fruits",
                    body="apple",
                    parsers=["ListEntityPlugin"],
                    score=1.0,
                    alternative_index=0,
                    alternative_indices=[0],
                    value="apple",
                    range={"start": 6, "end": 11},
                ),
                KeywordEntity(
                    entity_type="colour",
                    body="orange",
                    parsers=["ListEntityPlugin"],
                    score=0.0,
                    alternative_index=1,
                    alternative_indices=[1],
                    value="apple",
                    range={"start": 6, "end": 12},
                ),
                KeywordEntity(
                    entity_type="colour",
                    body="orange",
                    parsers=["ListEntityPlugin"],
                    score=0.5,
                    value="apple",
                    range={"start": 6, "end": 12},
                ),
            ],
        },
        {
            "data": '["hello orange"]',
            "entities": [{}],
        },
    ]
)


TEST_DATA_2 = pd.DataFrame(
    [
        {
            "data": json.dumps(["hello apple", "hello orange"]),
            "entities": [
                KeywordEntity(
                    entity_type="colour",
                    body="orange",
                    parsers=["ListEntityPlugin"],
                    score=0.5,
                    value="apple",
                    range={"start": 6, "end": 12},
                )
            ],
        },
    ]
)


def test_canonicalization_utility():
    input_ = Input(utterances=[[{"transcript": "hello apple"}]])
    input_, _ = workflow.run(input_)
    assert input_.clf_feature == ["MASK <fruits>"]


def test_canonicalization_transform():
    df = canonicalization.transform(TEST_DATA.copy())
    assert df["data"][0] == json.dumps(["MASK <fruits>", "MASK orange"])


def test_canonicalization_transform_check_alts():
    df = canonicalization.transform(TEST_DATA_2.copy())
    assert df["data"][0] == json.dumps(["MASK apple", "MASK orange"])


def test_canonicalization_non_transform():
    df = no_op_canonicalization.transform(TEST_DATA.copy())
    assert df["data"][0] == json.dumps(["hello apple", "hello orange"])

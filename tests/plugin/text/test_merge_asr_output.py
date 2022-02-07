import json

import pandas as pd
import pytest

from dialogy.base import Input
from dialogy.plugins import MergeASROutputPlugin
from dialogy.workflow import Workflow

merge_asr_output_plugin = MergeASROutputPlugin(
    dest="input.clf_feature", use_transform=True, input_column="data"
)


def test_merge_asr_output() -> None:
    """
    This case shows the merge in case there is only one option.
    """

    workflow = Workflow([merge_asr_output_plugin])
    input_ = Input(utterances=[[{"transcript": "hello world", "confidence": None}]])

    input_, _ = workflow.run(input_)
    assert input_["clf_feature"] == ["<s> hello world </s>"]


def test_merge_longer_asr_output() -> None:
    """
    This case shows the merge in case there are multiple options.
    """
    workflow = Workflow([merge_asr_output_plugin])
    input_ = Input(
        utterances=[
            [
                {"transcript": "hello world", "confidence": None},
                {"transcript": "hello word", "confidence": None},
                {"transcript": "jello world", "confidence": None},
            ]
        ]
    )

    input_, _ = workflow.run(input_)
    assert input_["clf_feature"] == [
        "<s> hello world </s> <s> hello word </s> <s> jello world </s>"
    ]


def test_merge_keyerror_on_missing_transcript() -> None:
    """
    This test, shows that `transcript` is an important key. If the asr has a different key, than `transcript`
    then this plugin would not work for you.
    """

    workflow = Workflow([merge_asr_output_plugin])
    input_ = Input(utterances=[[{"not_transcript": "hello world", "confidence": None}]])

    with pytest.raises(TypeError):
        workflow.run(input_)


def test_invalid_data() -> None:
    train_df = pd.DataFrame(
        [
            {"data": json.dumps([[{"transcript": "yes"}]])},
            {"data": json.dumps({})},
            {"data": ""},
        ]
    )
    train_df_ = merge_asr_output_plugin.transform(train_df)
    assert len(train_df) - len(train_df_) == 2

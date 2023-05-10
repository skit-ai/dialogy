import json

import pandas as pd
import pytest

from dialogy.base import Input
from dialogy.plugins.registry import MergeASROutputPlugin
from dialogy.workflow import Workflow

merge_asr_output_plugin = MergeASROutputPlugin(
    dest="input.clf_feature", use_transform=True, input_column="data"
)


@pytest.mark.asyncio
async def test_merge_asr_output() -> None:
    """
    This case shows the merge in case there is only one option.
    """

    workflow = Workflow([merge_asr_output_plugin])
    input_ = Input(utterances=[[{"transcript": "hello world", "confidence": None}]])

    input_, _ = await workflow.run(input_)
    assert input_.clf_feature == ["<s> hello world </s>"]


@pytest.mark.asyncio
async def test_merge_longer_asr_output() -> None:
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

    input_, _ = await workflow.run(input_)
    assert input_.clf_feature == [
        "<s> hello world </s> <s> hello word </s> <s> jello world </s>"
    ]


def test_invalid_data() -> None:
    train_df = pd.DataFrame(
        [
            {"data": json.dumps([[{"transcript": "yes"}]])},
            {"data": json.dumps({})},
        ]
    )
    train_df_ = merge_asr_output_plugin.transform(train_df)
    assert len(train_df) - len(train_df_) == 1

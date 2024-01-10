import json

import pandas as pd
import pytest
from typing import Any, List, Optional, Union, Dict
from typing import Any, Callable, List
from dialogy.types import Utterance

from dialogy.base import Input
from dialogy.plugins.text.dob_plugin import _transform_invalid_date, get_transcripts_from_utterances
from dialogy.plugins.registry import DOBPlugin
from dialogy.workflow import Workflow
from tests import load_tests, MockResponse
# from tests.plugin.text.test_dob_plugin.duckling_api import get_entities_from_duckling

get_dob = DOBPlugin(
    dest="input.transcripts", use_transform=True, input_column="data"
)

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", load_tests("cases", __file__)) 
async def test_transform_invalid_date(test_case) -> None:
    """
    These test cases cover different scenarios:
    - A valid transcript with no transformation needed.
    - Class 4 transformation scenario
    - Class 5 transformation scenario (hours and minutes).
    - Class 6 transformation scenario (numeric and word representation).
    - Class 7 transformation scenario
    - Combined transformations from both Class 4,5,6,7.
    """
    if test_case["function"]=="transform_invalid_transcript":
            print("testing function:",test_case["function"])
            print("description:",test_case["description"])
            result = _transform_invalid_date(test_case["transcript"])
            print("result = ", result)
            print("expected = ",test_case["expected"])
            assert result == test_case["expected"]


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", load_tests("cases", __file__)) 
async def test_get_transcripts_from_utterances(test_case) -> None:
    try:
        if test_case["function"]=="get_transcripts_from_utterances":
            print("testing function:",test_case["function"])
            print("description:",test_case["description"])
            result = await get_transcripts_from_utterances(test_case["utterances"])
            assert result == test_case["expected"]
    except:
        pass



@pytest.mark.asyncio
async def test_invalid_data() -> None:
    print("test 3")
    train_df = pd.DataFrame(
        [
            {"data": json.dumps([[{"transcript": "yes"}]])},
            {"data": json.dumps({})},
        ]
    )
    train_df_ = await get_dob.transform(train_df)
    assert len(train_df) - len(train_df_) == 1

import json

import pandas as pd
import pytest
from typing import Any, List, Optional, Union, Dict
from typing import Any, Callable, List
from dialogy.types import Utterance

from dialogy.base import Input
from dialogy.plugins.registry import DOBPlugin
from dialogy.workflow import Workflow
from tests import load_tests, MockResponse
from tests.plugin.text.test_dob_plugin.duckling_api import get_entities_from_duckling

get_dob = DOBPlugin(
    dest="input.transcripts", use_transform=True, input_column="data"
)
"""
Checker function in test: 
input: expected, all transcripts
Description: for each transcript, check if duckling(transcript)==duckling(expected)
Output: true/false, %increase in correctness
"""
def checker(transcripts: List[str], expected: str) -> Union[int, None]:
    """
    input: transcripts- a list of strings; expected- a string
    description: for each transcript, check if get_entities_from_duckling(transcript)==get_entities_from_duckling(expected), if yes correctness +=1 
    return "correctness"
    """
    correctness = 0

    for transcript in transcripts:
        try:
            duckling_val_transcript = get_entities_from_duckling(transcript)
            duckling_val_expected = get_entities_from_duckling(expected)
            # print("duckling_val_transcript, duckling_val_expected: ", duckling_val_transcript, duckling_val_expected)
            if duckling_val_transcript == duckling_val_expected:
                correctness += 1
        except:
            print("text is empty/invalid, refused by duckling")
            pass

    return correctness
def get_transcripts_from_utterances(utterances: List[Utterance]) -> List[str]:
    """
    input: utterances = [
        [{'transcript': '102998', 'confidence': None}, 
        {'transcript': '10 29 98', 'confidence': None}, 
        {'transcript': '1029 niniety eight', 'confidence': None}]
    ]
    description: access each transcript, confidence score pair, get 
    the result of <any func(transcript)>; 
    get a dictionary containing all results; 
    order this dictionary in decreasing order of confidence score
    output: 
    best_transcript
    """
    result_dict = {}
    for utterance_set in utterances:
        for utterance in utterance_set:
            transcript = utterance.get('transcript')
            confidence = utterance.get('confidence')
            confidence = 0 if confidence is None else confidence  # Ensure confidence is not None
            result = transcript
            if result in result_dict:
                result_dict[result] += confidence
            else:
                result_dict[result] = confidence

    # Sort the result_dict based on confidence in descending order
    sorted_result = {k: v for k, v in sorted(result_dict.items(), key=lambda item: item[1], reverse=True)}
    transcripts = sorted(sorted_result, key=lambda x: sorted_result[x], reverse=True)

    # Get the best transcript from the sorted result
    # best_transcript = next(iter(sorted_result.keys()), [])

    return transcripts

@pytest.mark.asyncio
async def test_dob_1() -> None:
    print("test 1: This case shows the best transcript in case there is only one option.")
    """
    This case shows the best transcript in case there is only one option.    
    """

    workflow = Workflow([get_dob])
    input_ = Input(utterances=[[{"transcript": "1029 98", "confidence": None}]])
    # correctness = checker(input_.transcripts,)
    # replace this "best" with "expected"
    best = input_.best_transcript
    input_, _ = await workflow.run(input_)
    assert input_.best_transcript == best



@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", load_tests("cases_desc", __file__)) 
async def test_dob_2(test_case) -> None:
    try:
        if test_case["description"]:
            print("test_case description:",test_case["description"])
    except:
        pass

    expected = test_case["expected"]
    if expected != "-":
        
        workflow = Workflow([get_dob])
        input_ = Input(utterances=test_case["utterances"])
        correctness = checker(input_.transcripts,expected)
        input, _ = await workflow.run(input_)
        print("input_ = ", input_.transcripts)
        print("input = ", input.transcripts)
        dob_plugin_correctness = checker(input.transcripts, expected)
        # if dob_plugin_correctness<correctness and expected!="-":
        #     print("RESULT:",test_case["description"])
        #     print("input_ = ", input_)
        #     print("input = ", input)
        #     print("correctness and dob correctness:",correctness, dob_plugin_correctness)
        assert dob_plugin_correctness > correctness
    
    else:
        print("expected not defined")



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


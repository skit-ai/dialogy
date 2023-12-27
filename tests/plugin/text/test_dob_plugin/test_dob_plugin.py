import json

import pandas as pd
import pytest

from dialogy.base import Input
from dialogy.plugins.registry import DOBPlugin
from dialogy.workflow import Workflow
from tests import load_tests, MockResponse

get_dob = DOBPlugin(
    dest="input.best_transcript", use_transform=True, input_column="data"
)
def get_best_transcript_from_utterances(utterances):
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
    # Get the best transcript from the sorted result
    best_transcript = next(iter(sorted_result.keys()), [])

    return best_transcript

@pytest.mark.asyncio
async def test_dob_1() -> None:
    print("test 1: This case shows the best transcript in case there is only one option.")
    """
    This case shows the best transcript in case there is only one option.    
    """

    workflow = Workflow([get_dob])
    input_ = Input(utterances=[[{"transcript": "1029 98", "confidence": None}]])
    # replace this "best" with "expected"
    best = input_.best_transcript
    input_, _ = await workflow.run(input_)
    assert input_.best_transcript == best


# @pytest.mark.asyncio
# @pytest.mark.parametrize("test_case", [
#     {
#         "utterances": [
#             {"confidence": 0.6564267, "transcript": "6 to 4:59"},
#             {"confidence": 0.65825063, "transcript": "6459"},
#             # Add more utterances as needed
#         ],
#         "expected": "6 to 4:59"
#     },
#     {
#         "utterances": [
#             {"confidence": 0.9128386, "transcript": "1576"},
#         ],
#         "expected": "1576"
#     },
#     {
#         "utterances": [
#             {"confidence": 0.6454812, "transcript": "7 2763"},
#             {"confidence": 0.39310354, "transcript": "7th 2763"},
#             # Add more utterances as needed
#         ],
#         "expected": "7 2763"
#     },
#     # Add more test cases as needed
# ])
# async def test_dob_2(test_case) -> None:
#     print("Running test case with expected:", test_case["expected"])
#     workflow = Workflow([get_dob])
#     input_ = Input(utterances=[test_case["utterances"]])
#     # expected = test_case["expected"]
#     expected = get_best_transcript_from_utterances(utterances = [test_case["utterances"]])
#     input_, _ = await workflow.run(input_)

#     assert input_.best_transcript == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", load_tests("cases", __file__))
async def test_dob_2(test_case) -> None:
    try:
        if test_case["description"]:
            print("test_case description:",test_case["description"])
    except:
        pass

    workflow = Workflow([get_dob])
    input_ = Input(utterances=test_case["utterances"])
    # expected = get_best_transcript_from_utterances(utterances=test_case["utterances"])
    expected = input_.best_transcript
    input_, _ = await workflow.run(input_)

    assert input_.best_transcript == expected


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

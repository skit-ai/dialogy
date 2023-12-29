import json
import traceback
from typing import Any, List, Optional, Union, Dict

import pandas as pd
from loguru import logger
from tqdm import tqdm

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.utils import normalize

def _transform_invalid_date(transcript):
    """
    input: transcripts that are responses for when the user is asked their 
    dob for authentication and are not recognised as dates by duckling
    output: trasnformed transcript recognised by duckling as date (closest valid date)
    """
    return transcript
import pdb
def get_transcripts_from_utterances(utterances, func_transcript):
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
    best_transcript,
    """
    result_dict = {}
    for utterance_set in utterances:
        for utterance in utterance_set:
            transcript = utterance.get('transcript')
            confidence = utterance.get('confidence')
            confidence = 0 if confidence is None else confidence  # Ensure confidence is not None
            result = func_transcript(transcript)
            if result in result_dict:
                result_dict[result] += confidence
            else:
                result_dict[result] = confidence

    # Sort the result_dict based on confidence in descending order
    sorted_result = {k: v for k, v in sorted(result_dict.items(), key=lambda item: item[1], reverse=True)}
    transcripts = sorted(sorted_result, key=lambda x: sorted_result[x], reverse=True)
    # print("transcripts = ", transcripts)
    # Get the best transcript from the sorted result
    # best_transcript = next(iter(sorted_result.keys()), [])

    return transcripts


def get_dob(utterances) -> str:  
    try:
        print("UTTERS:", utterances)
        transcripts = normalize(utterances)
        invalid_transcript = len(transcripts) == 1 and any(
            token.lower() in transcripts for token in const.INVALID_TOKENS
        )
        if invalid_transcript or not transcripts:
            return []
        else:
            # best_transcript = _format_date(utterances)
            transcripts = get_transcripts_from_utterances(utterances=utterances, func_transcript=_transform_invalid_date)
            print("dob output:",transcripts)
            return transcripts
    except TypeError as type_error:
        raise TypeError("`transcript` is expected in the ASR output.") from type_error


class DOBPlugin(Plugin):

    def __init__(
        self,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
            **kwargs
        )

    async def utility(self, input: Input, _: Output) -> Any:
        # return input.best_transcript
        return get_dob(input.utterances)

    async def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        if not self.use_transform:
            return training_data

        training_data["use"] = True
        logger.debug(f"Transforming dataset via {self.__class__.__name__}")
        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            asr_output = None
            try:
                asr_output = json.loads(row[self.input_column])
                if asr_output and (dob := get_dob(asr_output)):
                    training_data.loc[i, self.output_column] = dob[0]
                else:
                    training_data.loc[i, "use"] = False
            except Exception as error:  # pylint: disable=broad-except
                training_data.loc[i, "use"] = False
                logger.error(f"{error} -- {asr_output}\n{traceback.format_exc()}")

        training_data_ = training_data[training_data.use].copy()
        training_data_.drop("use", axis=1, inplace=True)
        discarded_data = len(training_data) - len(training_data_)
        if discarded_data:
            logger.debug(
                f"Discarding {discarded_data} samples because the alternatives couldn't be parsed."
            )
        return training_data_

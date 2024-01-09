import json
import re
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
from loguru import logger
from tqdm import tqdm
from word2number import w2n

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import Utterance
from dialogy.utils import normalize

def _post_processing_clean(transformed_transcript: str) -> str:
    transformed_transcript = transformed_transcript.strip()
    if "  "in transformed_transcript:
        transformed_transcript = transformed_transcript.replace("  ", " ")
    return transformed_transcript

def _class_7_1(transcript: str) -> str:
    """
    replace all instances that look like this: 
        <1 or 2 digit number><space><4 digit number> with 
        <1 or 2 digit number><space><2 digit number><2 digit number>
    """
    try:
        pattern = r'^\b(\d{1,2})\s(\d{2})(\d{2})\b$'
        match = re.search(pattern, transcript)
        if match:
            # Access matching groups using group() or groups()
            full_match = match.group(0)
            print("groups = ",match.group(1), match.group(2), match.group(3))
            initial = match.group(1)
            two_digit_number_1 = match.group(2)
            two_digit_number_2 = match.group(3)
            split_four_into_2_two_digit_numbers = initial+" "+two_digit_number_1+" "+two_digit_number_2
            return _post_processing_clean(split_four_into_2_two_digit_numbers)
        else:
            return transcript
    except:
        return transcript

def _class_4(input_string: str) -> str:
    """
    cleaining
    """
    # Remove all instances of "."
    cleaned_string = input_string.replace(".", " ")
    # Remove all instances of "it's" (case insensitive)
    cleaned_string = cleaned_string.replace("it's", " ")
    # replace all instances of "for" with 4 (case insensitive)
    cleaned_string = cleaned_string.replace("for", "4")
    # replace all instances of "-" with " " (case insensitive)
    cleaned_string = cleaned_string.replace("-", " ")
    # replace all instances of "st/nd/rd/th" with "" (case insensitive)
    cleaned_string = re.sub(r'(\d+)(?:st|nd|rd|th)', r'\1', cleaned_string)


    cleaned_string = _post_processing_clean(cleaned_string)
    return cleaned_string


def _class_6(transcript: str) -> str:
    """
    input: transcript that looks like- " X Y" where X is a string of numbers with or without space. Y is string- which is a
    number written in words.
    description: let X be as is. Only if X exist, look for Y. then convert Y into numbers- numeric digits
    output: X (as is) Y(converted into numbers)
    """
    """
    logic: WILL ONLY HANDLE YY IN WORDS!, NOT YYYY
    1. regex pattern- 
        2 groups- 
        1st: numeric characters- with or without space; 
        2nd: everything that follows it - alphanumeric characters 
        start_idx = starting index of group 1
    2. let group 1 be as is
    3. transform group 2:
        1. only retain the part that is a word representation of some number. end_idx = last index of this word representation of number
        2. convert this word representation of number to numbers = words_converted_to_number
    4. new_substring = group 1 + words_converted_to_number
    5. replace the start_idx to last_idx part of the original string with new_substring
    6. return transformed string
        """

    # Regex pattern to capture numeric part and remaining words separately
    pattern = re.compile(r"(\b\d+\s*\d*\b|\b\d+\b)(.*)", re.IGNORECASE)

    match = re.search(pattern, transcript)

    if match:
        numeric_part = match.group(1)
        remaining_words = match.group(2) or ""
        try:
            words_converted_to_number = str(w2n.word_to_num(remaining_words))
            if len(words_converted_to_number) <= 2:

                # Construct the transformed substring
                transformed_transcript = numeric_part + " " + words_converted_to_number
                return _post_processing_clean(transformed_transcript)
        except:
            pass
    return transcript  # Return original transcript if no match


def _class_5(transcript: str) -> str:
    """
    input: transcript that looks like-"xx:yy "
    description: replace ":" with " "; if yy = 00 or 0y: replace yy with "  " or if 0y, replace 0 with ""
    output: xx yy
    """

    # Your regex pattern
    pattern = re.compile(r"\b(\d{1,2}):(\d{2})\b")

    match = pattern.search(transcript)

    if match:
        hours, minutes = match.groups()
        start_idx, hours_end = match.start(1), match.end(1)
        minutes_start, end_idx = match.start(2), match.end(2)

        # Modifying the minutes based on the conditions
        if minutes == "00":
            minutes = ""
        elif minutes.startswith("0"):
            minutes = "" + minutes[1]

        # Combining the modified hours and minutes
        result = hours + " " + minutes
        transformed_transcript = transcript[:start_idx] + result + transcript[end_idx:]
        return _post_processing_clean(transformed_transcript)

    else:
        # Handle invalid input
        return transcript


def _transform_invalid_date(transcript: str) -> str:
    """
    input: transcripts that are responses for when the user is asked their
    dob for authentication and are not recognised as dates by duckling
    output: trasnformed transcript recognised by duckling as date (closest valid date)
    description: handling class 5 error
    """
    transcript = _class_4(transcript)
    transcript = _class_5(transcript)
    transcript = _class_6(transcript)    
    transcript = _class_7_1(transcript)
    return transcript


def get_transcripts_from_utterances(
    utterances: List[Utterance], func_transcript: Callable[[str], str]
) -> List[str]:
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
    result_dict: Dict[str, Any] = {}
    transcripts: List[str] = []

    for utterance_set in utterances:
        for utterance in utterance_set:
            transcript = utterance.get("transcript", "")
            confidence = utterance.get("confidence", 0)

            confidence = (
                0 if confidence is None else confidence
            )  # Ensure confidence is not None
            result = func_transcript(str(transcript))
            if result == None:
                result = ""
                confidence = 0
            if result in result_dict:
                result_dict[result] += confidence
            else:
                result_dict[result] = confidence

    # Sort the result_dict based on confidence in descending order
    sorted_result = {
        k: v
        for k, v in sorted(result_dict.items(), key=lambda item: item[1], reverse=True)
        if v is not None
    }
    transcripts = sorted(sorted_result, key=lambda x: sorted_result[x], reverse=True)

    return transcripts


def get_dob(utterances: List[Utterance]) -> List[str]:
    try:
        # print("UTTERS:", utterances)
        transcripts = normalize(utterances)
        invalid_transcript = len(transcripts) == 1 and any(
            token.lower() in transcripts for token in const.INVALID_TOKENS
        )
        if invalid_transcript or not transcripts:
            return []
        else:
            # best_transcript = _format_date(utterances)
            # print("transcripts = ", transcripts)
            transcripts = get_transcripts_from_utterances(
                utterances=utterances, func_transcript=_transform_invalid_date
            )
            # print("dob output:",transcripts)
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
        **kwargs: Any,
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
            **kwargs,
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

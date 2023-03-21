"""
    This module consist of custom functions that operate on primitives such as transcripts, intents and entities

"""

from dialogy.types import BaseEntity, Intent
from typing import List
import copy

# The below custom functions are coming in from ashley's StateToIntent code wherein we need to count the number of digits and check if a number is present in more than 50% of transcripts


def is_number_absent(transcripts: List[str]) -> bool:
    num_transcripts_with_digits = 0
    for word in transcripts:
        if any(char.isdigit() for char in word):
            num_transcripts_with_digits += 1
    if (
        num_transcripts_with_digits / len(transcripts)
    ) > 0.5:  # consider it as a number only if a number is present in more than 50% of the transcripts
        return False
    return True


def contain_digits(ner_input: List[str], threshold: int = 5) -> bool:
    first_alternative = ner_input[0]
    return sum(c.isdigit() for c in first_alternative) >= threshold

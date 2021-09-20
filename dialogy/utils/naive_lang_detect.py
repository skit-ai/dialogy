import re
from typing import List, Union


def _lang_detect(text: str) -> str:
    text = re.sub(r"[^a-z\u0900-\u0c7f]+", " ", text.lower())
    maxchar = max(text)
    if "\u0c00" <= maxchar <= "\u0c7f":
        return "te"
    if "\u0900" <= maxchar <= "\u097f":
        return "hi"
    return "en"


def lang_detect_from_text(text: Union[str, List[str]]) -> str:
    if isinstance(text, str):
        return _lang_detect(text)
    if text and isinstance(text, list):
        return _lang_detect(" ".join(text))
    raise TypeError(f"{text=} must be a string or a list of strings")

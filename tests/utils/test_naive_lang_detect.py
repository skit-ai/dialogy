import pytest
from dialogy.utils import lang_detect_from_text


def test_en_lang_detect_from_text():
    text = "hello!"
    strings = ["hello"]
    assert lang_detect_from_text(text) == "en"
    assert lang_detect_from_text(strings) == "en"


def test_hi_lang_detect_from_text():
    text = "हां"
    strings = ["हां"]
    assert lang_detect_from_text(text) == "hi"
    assert lang_detect_from_text(strings) == "hi"


def test_te_lang_detect_from_text():
    text = "హలో"
    strings = ["హలో"]
    assert lang_detect_from_text(text) == "te"
    assert lang_detect_from_text(strings) == "te"


def test_lang_detect_invalid():
    with pytest.raises(TypeError):
        lang_detect_from_text(None)

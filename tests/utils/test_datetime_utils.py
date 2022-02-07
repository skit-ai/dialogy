import pytest
from dialogy.utils import make_unix_ts


def test_tz_aware_ts():
    assert make_unix_ts("Asia/Kolkata")("2022-02-07T19:36:37.188396+05:30") == 1644242797188


def test_tz_unaware_ts():
    assert make_unix_ts("Asia/Kolkata")("2022-02-07T19:39:39.537827") == 1644241599537


def test_incorrect_tz():
    with pytest.raises(ValueError):
        make_unix_ts(None)("2022-02-07T19:36:37.188396")


def test_int_returned_as_is():
    make_unix_ts(None)(1644241599537) == 1644241599537

import json
import os
import pathlib
from typing import Any, Callable, List

from pydantic import ValidationError

import pytz
import yaml

EXCEPTIONS = {
    "TypeError": TypeError,
    "KeyError": KeyError,
    "ValueError": ValueError,
    "NotImplementedError": NotImplementedError,
    "UnknownTimeZoneError": pytz.UnknownTimeZoneError,
    "ValidationError": ValidationError,
}


def load_tests(test_type, current_path, ext=".yaml"):
    test_dir = pathlib.Path(current_path).parent
    test_cases_path = os.path.join(test_dir, f"test_{test_type}{ext}")
    with open(test_cases_path, "r") as handle:
        if ext == ".yaml":
            test_cases = yaml.load(handle, Loader=yaml.FullLoader)
        elif ext == ".json":
            test_cases = json.load(handle)
        # make any suitable modifications here
    return test_cases


def request_builder(
    expected_response, response_code=200
) -> Callable[[Any, Any, Any], List[Any]]:
    header = "application/x-www-form-urlencoded; charset=UTF-8"

    def request_callback(request, _, response_headers) -> List[Any]:
        content_type = request.headers.get("Content-Type")
        assert (
            content_type == header
        ), f"expected {header} but received Content-Type: {content_type}"
        return [response_code, response_headers, json.dumps(expected_response)]

    return request_callback


class MockResponse:
    def __init__(self, text, status):
        self._text = text
        self.status = status

    async def text(self):
        return self._text

    async def json(self):
        return json.loads(self._text)

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def __aenter__(self):
        return self
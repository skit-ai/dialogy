import json
import os
import pathlib
from typing import Any, Callable, List

import yaml

EXCEPTIONS = {"TypeError": TypeError, "KeyError": KeyError, "ValueError": ValueError}


def load_tests(test_type, current_path):
    test_dir = pathlib.Path(current_path).parent
    test_cases_path = os.path.join(test_dir, f"test_{test_type}.yaml")
    with open(test_cases_path, "r") as handle:
        test_cases = yaml.load(handle, Loader=yaml.FullLoader)
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

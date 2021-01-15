import json
import pytest
import httpretty
import requests
from dialogy.parsers.text.entities import DucklingParser


@httpretty.activate
def test_duckling_api_success():
    """
    Initialize DucklingParser and `.get_entities`.

    This test-case bypasses duckling API calls via httpretty. The expected response
    was originally generated using:

    ```
    curl -XPOST http://0.0.0.0:8000/parse \\
        --data 'locale=en_US&text="I need four of those on 27th next month. Can I have it at 5 am""&dims="[date"]"'
    ```
    """
    body = "I need four of those on 27th next month. Can I have it at 5 am"
    duckling_header = "application/x-www-form-urlencoded; charset=UTF-8"
    expected_response = [
        {
            "body": "four",
            "start": 7,
            "value": {"value": 4, "type": "value"},
            "end": 11,
            "dim": "number",
            "latent": False,
        },
        {
            "body": "on 27th next month",
            "start": 21,
            "value": {
                "values": [
                    {
                        "value": "2021-01-27T00:00:00.000-08:00",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-01-27T00:00:00.000-08:00",
                "grain": "day",
                "type": "value",
            },
            "end": 39,
            "dim": "time",
            "latent": False,
        },
        {
            "body": "at 5 am",
            "start": 55,
            "value": {
                "values": [
                    {
                        "value": "2020-12-24T05:00:00.000-08:00",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2020-12-25T05:00:00.000-08:00",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2020-12-26T05:00:00.000-08:00",
                        "grain": "hour",
                        "type": "value",
                    },
                ],
                "value": "2020-12-24T05:00:00.000-08:00",
                "grain": "hour",
                "type": "value",
            },
            "end": 62,
            "dim": "time",
            "latent": False,
        },
    ]

    def request_callback(request, _, response_headers):
        content_type = request.headers.get("Content-Type")
        assert (
            content_type == duckling_header
        ), f"expected {duckling_header} but received Content-Type: {content_type}"
        return [200, response_headers, json.dumps(expected_response)]

    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(transformers=[], dimensions=["date"], locale="en_IN")

    response = parser.get_entities(body, None)
    assert response == expected_response


@httpretty.activate
def test_duckling_api_failure():
    """
    Simulate Duckling returning 500.
    """
    body = "27th next month"
    duckling_header = "application/x-www-form-urlencoded; charset=UTF-8"
    expected_response = [
        {
            "body": "27th next month",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2021-01-27T00:00:00.000-08:00",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-01-27T00:00:00.000-08:00",
                "grain": "day",
                "type": "value",
            },
            "end": 15,
            "dim": "time",
            "latent": False,
        }
    ]

    def request_callback(request, _, response_headers):
        content_type = request.headers.get("Content-Type")
        assert (
            content_type == duckling_header
        ), f"expected {duckling_header} but received Content-Type: {content_type}"
        return [500, response_headers, json.dumps(expected_response)]

    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(transformers=[], dimensions=["date"], locale="en_IN")

    with pytest.raises(ValueError):
        parser.get_entities(body, None)

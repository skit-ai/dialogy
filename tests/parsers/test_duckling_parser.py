import json

import pytest
import pytz
import httpretty
import requests
from typing import List

from dialogy.parsers.text.entities import DucklingParser
from dialogy.workflow import Workflow
from dialogy.types.entities import (
    BaseEntity,
    NumericalEntity,
    PeopleEntity,
    TimeIntervalEntity,
    TimeEntity,
)


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

    parser = DucklingParser(locale="en_IN")

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

    parser = DucklingParser(dimensions=["time"], locale="en_IN")

    with pytest.raises(ValueError):
        parser.get_entities(body, None)


@httpretty.activate
def test_duckling_with_tz():
    """
    Simulate Duckling returning 500.
    """
    body = "i need it at 4 am"
    duckling_header = "application/x-www-form-urlencoded; charset=UTF-8"
    expected_response = [
        {
            "body": "4 am",
            "start": 7,
            "value": {
                "values": [
                    {
                        "value": "2021-01-21T04:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2021-01-22T04:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2021-01-23T04:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                ],
                "value": "2021-01-21T04:00:00.000+05:30",
                "grain": "hour",
                "type": "value",
            },
            "end": 11,
            "dim": "time",
            "latent": False,
        }
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

    parser = DucklingParser(locale="en_IN", timezone="Asia/Kolkata")

    response = parser.get_entities(body, None)
    assert response == expected_response


def test_duckling_wrong_tz():
    """
    Simulate Duckling returning 500.
    """
    body = "i need it at 4 am"
    duckling_header = "application/x-www-form-urlencoded; charset=UTF-8"

    def request_callback(request, _, response_headers):
        content_type = request.headers.get("Content-Type")
        assert (
            content_type == duckling_header
        ), f"expected {duckling_header} but received Content-Type: {content_type}"
        return [200, response_headers, json.dumps({})]

    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(locale="en_IN", timezone="Earth/Someplace")

    with pytest.raises(pytz.UnknownTimeZoneError):
        response = parser.get_entities(body, None)


def test_entity_mutation_dict():
    entities_json = {
        "body": "four",
        "start": 7,
        "value": {"value": 4, "type": "value"},
        "end": 11,
        "dim": "number",
        "latent": False,
    }

    parser = DucklingParser(locale="en_IN")

    entity = parser.mutate_entity(entities_json)

    assert "range" in entity
    assert "start" in entity["range"]
    assert "end" in entity["range"]
    assert "values" in entity
    assert entity["values"][0]["value"] == 4


def test_entity_mutation_list():
    entity_json = {
        "body": "at 5 am",
        "start": 55,
        "value": {
            "values": [
                {
                    "value": "2021-01-21T05:00:00.000+05:30",
                    "grain": "hour",
                    "type": "value",
                },
                {
                    "value": "2021-01-22T05:00:00.000+05:30",
                    "grain": "hour",
                    "type": "value",
                },
                {
                    "value": "2021-01-23T05:00:00.000+05:30",
                    "grain": "hour",
                    "type": "value",
                },
            ],
            "value": "2021-01-21T05:00:00.000+05:30",
            "grain": "hour",
            "type": "value",
        },
        "end": 62,
        "dim": "time",
        "latent": False,
    }

    parser = DucklingParser(locale="en_IN")

    entity = parser.mutate_entity(entity_json)

    assert "range" in entity
    assert "start" in entity["range"]
    assert "end" in entity["range"]
    assert "values" in entity
    assert "value" not in entity
    assert entity["values"][0]["value"] == "2021-01-21T05:00:00.000+05:30"


def test_entity_json_to_object_time_entity():
    parser = DucklingParser(locale="en_IN")
    entities_json = [
        {
            "body": "at 5 am",
            "start": 55,
            "value": {
                "values": [
                    {
                        "value": "2021-01-21T05:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2021-01-22T05:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                    {
                        "value": "2021-01-23T05:00:00.000+05:30",
                        "grain": "hour",
                        "type": "value",
                    },
                ],
                "value": "2021-01-21T05:00:00.000+05:30",
                "grain": "hour",
                "type": "value",
            },
            "end": 62,
            "dim": "time",
            "latent": False,
        }
    ]

    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], TimeEntity)


def test_entity_json_to_object_time_interval_entity():
    parser = DucklingParser(locale="en_IN")
    entities_json = [
        {
            "body": "between 2 to 4 am",
            "start": 0,
            "value": {
                "values": [
                    {
                        "to": {
                            "value": "2021-01-22T05:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "from": {
                            "value": "2021-01-22T02:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "type": "interval",
                    },
                    {
                        "to": {
                            "value": "2021-01-23T05:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "from": {
                            "value": "2021-01-23T02:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "type": "interval",
                    },
                    {
                        "to": {
                            "value": "2021-01-24T05:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "from": {
                            "value": "2021-01-24T02:00:00.000+05:30",
                            "grain": "hour",
                        },
                        "type": "interval",
                    },
                ],
                "to": {"value": "2021-01-22T05:00:00.000+05:30", "grain": "hour"},
                "from": {"value": "2021-01-22T02:00:00.000+05:30", "grain": "hour"},
                "type": "interval",
            },
            "end": 17,
            "dim": "time",
            "latent": False,
        }
    ]

    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], TimeIntervalEntity)


def test_entity_json_to_object_numerical_entity():
    entities_json = [
        {
            "body": "four",
            "start": 7,
            "value": {"value": 4, "type": "value"},
            "end": 11,
            "dim": "number",
            "latent": False,
        }
    ]
    parser = DucklingParser(locale="en_IN")
    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], NumericalEntity)


def test_entity_json_to_object_people_entity():
    entities_json = [
        {
            "body": "3 people",
            "start": 67,
            "value": {"value": 3, "type": "value", "unit": "person"},
            "end": 75,
            "dim": "people",
            "latent": False,
        }
    ]
    parser = DucklingParser(locale="en_IN")
    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], PeopleEntity)


def test_entity_object_not_implemented():
    entities_json = [
        {
            "body": "3 foobars",
            "start": 67,
            "value": {"value": 3, "type": "foobar", "unit": "person"},
            "end": 75,
            "dim": "number",
            "latent": False,
        }
    ]
    parser = DucklingParser(locale="en_IN")

    with pytest.raises(NotImplementedError):
        parser.reshape(entities_json)


def test_entity_object_error_on_missing_value():
    entities_json = [
        {
            "body": "3 people",
            "start": 67,
            "end": 75,
            "dim": "people",
            "latent": False,
        }
    ]
    parser = DucklingParser(locale="en_IN")

    with pytest.raises(KeyError):
        parser.reshape(entities_json)


def test_plugin_io_missing():
    parser = DucklingParser(locale="en_IN")
    plugin = parser.exec()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


def test_plugin_io_type_mismatch():
    parser = DucklingParser(access=5, mutate=54, locale="en_IN")
    plugin = parser.exec()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


@httpretty.activate
def test_plugin():
    """
    [summary]

    Returns:
        [type]: [description]
    """
    body = "I need it for 4 people."
    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}
    
    duckling_header = "application/x-www-form-urlencoded; charset=UTF-8"
    parser = DucklingParser(access=access, mutate=mutate, dimensions=["people"], locale="en_IN")
    expected_response = [
        {
            "body": "4 people",
            "start": 14,
            "value": {"value": 4, "type": "value", "unit": "person"},
            "end": 22,
            "dim": "people",
            "latent": False,
        }
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

    workflow = Workflow(preprocessors=[parser.parse], postprocessors=[])
    workflow.run(body)
    assert isinstance(workflow.output["entities"][0], PeopleEntity)

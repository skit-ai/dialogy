import json
from typing import Any, Callable, List

import httpretty
import pytest
import pytz

from dialogy.parser.text.entity import DucklingParser
from dialogy.types.entity import (
    DurationEntity,
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
)
from dialogy.workflow import Workflow
from tests.parser.text.entity import config


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


# == Test successful api call ==
@httpretty.activate
def test_duckling_api_success() -> None:
    """
    Initialize DucklingParser and `.get_entities`.

    This test-case bypasses duckling API calls via httpretty. The expected response
    was originally generated using:

    ```shell

    export month_q="I need four of those on 27th next month."
    export time_q="Can I have it at 5 am""&dims="[date"]"
    export text="$month_q $time_q"
    curl -XPOST http://0.0.0.0:8000/parse --data 'locale=en_US&text=$text'
    ```
    """
    body = "I need four of those on 27th next month. Can I have it at 5 am"

    expected_response = [
        config.mock_number_entity,
        config.mock_date_entity,
        config.mock_time_entity,
    ]

    request_callback = request_builder(expected_response)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(
        dimensions=["number", "date", "time"], timezone="Asia/Kolkata", locale="en_IN"
    )

    response = parser.get_entities(body)
    assert response == expected_response


# == Test duckling api returning 500 ==
@httpretty.activate
def test_duckling_api_failure() -> None:
    """
    Simulate Duckling returning 500.
    """
    body = "27th next month"
    expected_response = [config.mock_date_entity]

    request_callback = request_builder(expected_response, response_code=500)

    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(
        dimensions=["time"], locale="en_IN", timezone="Asia/Kolkata"
    )

    with pytest.raises(ValueError):
        parser.get_entities(body)


# == Test duckling with timezone info ==
@httpretty.activate
def test_duckling_with_tz() -> None:
    """
    Using DucklingParser with timezone.
    """
    body = "i need it at 5 am"
    expected_response = [config.mock_time_entity]

    request_callback = request_builder(expected_response)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(
        locale="en_IN", timezone="Asia/Kolkata", dimensions=["time"]
    )

    response = parser.get_entities(body)
    assert response == expected_response


# == Test duckling with incorrect timezone ==
def test_duckling_wrong_tz() -> None:
    """
    In case the timezone is incorrect or exceptions need to be handled.
    """
    body = "i need it at 5 am"

    request_callback = request_builder({})
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    parser = DucklingParser(
        locale="en_IN", timezone="Earth/Someplace", dimensions=["time"]
    )

    with pytest.raises(pytz.UnknownTimeZoneError):
        _ = parser.get_entities(body)


# == Test entity structure modifications for numerical entities ==
def test_entity_mutation_dict() -> None:
    """
    This piece of code is run by DucklingParser when the Duckling API
    returns a set of entities. There are a few keys added/removed.
    We are making sure of those for numerical entities here.
    """
    entities_json = config.mock_number_entity
    parser = DucklingParser(
        locale="en_IN", dimensions=["number"], timezone="Asia/Kolkata"
    )
    entity = parser.mutate_entity(entities_json)

    assert "range" in entity
    assert "start" in entity["range"]
    assert "end" in entity["range"]
    assert "values" in entity
    assert entity["values"][0]["value"] == 4


# == Test entity structure modifications for time entities ==
def test_entity_mutation_list() -> None:
    """
    This piece of code is run by DucklingParser when the Duckling API
    returns a set of entities. There are a few keys added/removed.
    We are making sure of those for time entities here.
    """
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

    parser = DucklingParser(
        locale="en_IN", dimensions=["time"], timezone="Asia/Kolkata"
    )
    entity = parser.mutate_entity(entity_json)

    assert "range" in entity
    assert "start" in entity["range"]
    assert "end" in entity["range"]
    assert "values" in entity
    assert "value" not in entity
    assert entity["values"][0]["value"] == "2021-01-21T05:00:00.000+05:30"


# == Test transformation of entity-json to TimeEntity ==
def test_entity_json_to_object_time_entity() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for TimeEntity here.
    """
    parser = DucklingParser(
        locale="en_IN", dimensions=["time"], timezone="Asia/Kolkata"
    )
    entities_json = [config.mock_time_entity]

    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], TimeEntity)


# == Test transformation of entity-json to TimeIntervalEntity ==
def test_entity_json_to_object_time_interval_entity():
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for TimeIntervalEntity here.
    """
    parser = DucklingParser(
        locale="en_IN", dimensions=["time"], timezone="Asia/Kolkata"
    )
    entities_json = [config.mock_interval_entity]

    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], TimeIntervalEntity)


# == Test transformation of entity-json to NumericalEntity ==
def test_entity_json_to_object_numerical_entity() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for NumericalEntity here.
    """
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
    parser = DucklingParser(
        locale="en_IN", dimensions=["number"], timezone="Asia/Kolkata"
    )
    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], NumericalEntity)


# == Test transformation of entity-json to DurationEntity ==
def test_entity_json_to_object_duration_entity() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for NumericalEntity here.
    """
    entities_json = [
        {
            "body": "2 days",
            "start": 0,
            "value": {
                "value": 2,
                "day": 2,
                "type": "value",
                "unit": "day",
                "normalized": {"value": 172800, "unit": "second"},
            },
            "end": 6,
            "dim": "duration",
            "latent": False,
        }
    ]
    parser = DucklingParser(
        dimensions=["duration"], locale="en_IN", timezone="Asia/Kolkata"
    )
    entities = parser.reshape(entities_json)
    print(entities)
    if not isinstance(entities[0], DurationEntity):
        pytest.fail("expected entities.")


# == Test transformation of entity-json to PeopleEntity ==
def test_entity_json_to_object_people_entity() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for PeopleEntity here.

    """
    entities_json = [config.mock_people_entity]
    parser = DucklingParser(
        locale="en_IN", dimensions=["people"], timezone="Asia/Kolkata"
    )
    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], PeopleEntity)


# == Test transformation of unknown entity type ==
def test_entity_object_not_implemented() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for an unknown entity type here.
    This would lead to a `NotImplementedError`.
    """
    entities_json = [config.mock_unknown_entity]
    parser = DucklingParser(
        locale="en_IN", dimensions=["unknown"], timezone="Asia/Kolkata"
    )

    with pytest.raises(NotImplementedError):
        parser.reshape(entities_json)


# == Test transormation of entity-json with missing value. ==
def test_entity_object_error_on_missing_value() -> None:
    """
    This json has missing `value` key. We can see that we will get a
    `KeyError` raised, this happens during the validation phase.
    """
    entities_json = [
        {
            "body": "3 people",
            "start": 67,
            "end": 75,
            "dim": "people",
            "latent": False,
        }
    ]
    parser = DucklingParser(
        locale="en_IN", timezone="Asia/Kolkata", dimensions=["people"]
    )

    with pytest.raises(KeyError):
        parser.reshape(entities_json)


# == Test missing i/o ==
def test_plugin_io_missing() -> None:
    """
    Here we are checking if the plugin has access to workflow.
    Since we haven't provided `access`, `mutate` to `DucklingParser`
    we will receive a `TypeError`.
    """
    parser = DucklingParser(
        locale="en_IN", timezone="Asia/Kolkata", dimensions=["time"]
    )
    plugin = parser()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


# == Test invalid i/o ==
@pytest.mark.parametrize(
    "access,mutate",
    [
        (1, 1),
        (lambda x: x, 1),
        (1, lambda x: x),
    ],
)
def test_plugin_io_type_mismatch(access, mutate) -> None:
    """
    Here we are chcking if the plugin has access to workflow.
    Since we have provided `access`, `mutate` of incorrect types to `DucklingParser`
    we will receive a `TypeError`.
    """
    parser = DucklingParser(
        access=access,
        mutate=mutate,
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
    )
    plugin = parser()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


# == Test plugin usage with Worfklow ==
@pytest.mark.parametrize(
    "body,expected",
    [
        (
            "I need it for 3 people.",
            [
                {
                    "body": "4 people",
                    "start": 14,
                    "value": {"value": 4, "type": "value", "unit": "person"},
                    "end": 22,
                    "dim": "people",
                    "latent": False,
                }
            ],
        ),
        (
            ["I need it for 3 people."],
            [
                {
                    "body": "4 people",
                    "start": 14,
                    "value": {"value": 4, "type": "value", "unit": "person"},
                    "end": 22,
                    "dim": "people",
                    "latent": False,
                }
            ],
        ),
    ],
)
@httpretty.activate
def test_plugin(body, expected) -> None:
    """
    An end-to-end example showing how to use `DucklingParser` with a `Worflow`.
    """

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingParser(
        access=access,
        mutate=mutate,
        dimensions=["people"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder(expected)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])
    workflow.run(body)
    assert isinstance(workflow.output["entities"][0], PeopleEntity)


# Test plugin with no possible entity from input.
@httpretty.activate
def test_plugin_no_entities() -> None:
    """
    An end-to-end example showing how `DucklingParser` works in case
    the input has no entities.
    """
    body = "i need it"
    expected = []

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingParser(
        access=access,
        mutate=mutate,
        dimensions=["people"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder(expected)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])
    workflow.run(body)
    assert workflow.output["entities"] == []


@pytest.mark.parametrize(
    "body",
    [42, None, {"key", 42}, [12]],
)
@httpretty.activate
def test_plugin_type_errors(body) -> None:
    """
    An end-to-end example showing how `DucklingParser` works in case
    the input is invalid.
    """

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingParser(
        access=access,
        mutate=mutate,
        dimensions=["people"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder([])
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    with pytest.raises(TypeError):
        workflow = Workflow(preprocessors=[parser()], postprocessors=[])
        workflow.run(body)


@httpretty.activate
def test_plugin_value_errors() -> None:
    """
    An end-to-end example showing how `DucklingParser` works in case
    the input is invalid.
    """

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingParser(
        access=access,
        mutate=mutate,
        dimensions=["people"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder([], response_code=500)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    with pytest.raises(ValueError):
        workflow = Workflow(preprocessors=[parser()], postprocessors=[])
        workflow.run("")

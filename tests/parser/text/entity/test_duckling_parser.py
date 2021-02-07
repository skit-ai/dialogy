import json
from typing import List, Any, Callable

import pytest
import pytz
import httpretty

from dialogy.parser.text.entity import DucklingParser
from dialogy.workflow import Workflow
from tests.parser.text.entity import config
from dialogy.types.entity import (
    NumericalEntity,
    PeopleEntity,
    TimeIntervalEntity,
    TimeEntity,
)


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

    parser = DucklingParser(locale="en_IN")

    response = parser.get_entities(body, None)
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

    parser = DucklingParser(dimensions=["time"], locale="en_IN")

    with pytest.raises(ValueError):
        parser.get_entities(body, None)


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

    parser = DucklingParser(locale="en_IN", timezone="Asia/Kolkata")

    response = parser.get_entities(body, None)
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

    parser = DucklingParser(locale="en_IN", timezone="Earth/Someplace")

    with pytest.raises(pytz.UnknownTimeZoneError):
        response = parser.get_entities(body, None)


# == Test entity structure modifications for numerical entities ==
def test_entity_mutation_dict() -> None:
    """
    This piece of code is run by DucklingParser when the Duckling API
    returns a set of entities. There are a few keys added/removed.
    We are making sure of those for numerical entities here.
    """
    entities_json = config.mock_number_entity
    parser = DucklingParser(locale="en_IN")
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

    parser = DucklingParser(locale="en_IN")
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
    parser = DucklingParser(locale="en_IN")
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
    parser = DucklingParser(locale="en_IN")
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
    parser = DucklingParser(locale="en_IN")
    entities = parser.reshape(entities_json)
    assert isinstance(entities[0], NumericalEntity)


# == Test transformation of entity-json to PeopleEntity ==
def test_entity_json_to_object_people_entity() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for PeopleEntity here.

    """
    entities_json = [config.mock_people_entity]
    parser = DucklingParser(locale="en_IN")
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
    parser = DucklingParser(locale="en_IN")

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
    parser = DucklingParser(locale="en_IN")

    with pytest.raises(KeyError):
        parser.reshape(entities_json)


# == Test missing i/o ==
def test_plugin_io_missing() -> None:
    """
    Here we are chcking if the plugin has access to workflow.
    Since we haven't provided `access`, `mutate` to `DucklingParser`
    we will receive a `TypeError`.
    """
    parser = DucklingParser(locale="en_IN")
    plugin = parser()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


# == Test invalid i/o ==
def test_plugin_io_type_mismatch() -> None:
    """
    Here we are chcking if the plugin has access to workflow.
    Since we have provided `access`, `mutate` of incorrect types to `DucklingParser`
    we will receive a `TypeError`.
    """
    parser = DucklingParser(access=5, mutate=54, locale="en_IN")
    plugin = parser()

    workflow = Workflow(preprocessors=[plugin], postprocessors=[])
    with pytest.raises(TypeError):
        workflow.run("")


# == Test plugin usage with Worfklow ==
@httpretty.activate
def test_plugin() -> None:
    """
    An end-to-end example showing how to use `DucklingParser` with a `Worflow`.
    """
    body = "I need it for 3 people."

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingParser(
        access=access, mutate=mutate, dimensions=["people"], locale="en_IN"
    )

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

    request_callback = request_builder(expected_response)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])
    workflow.run(body)
    assert isinstance(workflow.output["entities"][0], PeopleEntity)

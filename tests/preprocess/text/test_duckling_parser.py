import importlib
import json
import os
import pathlib
from typing import Any, Callable, List

import httpretty
import pytest
import pytz
import yaml

from dialogy.preprocess.text.duckling_plugin import DucklingPlugin
from dialogy.workflow import Workflow
from tests.preprocess.text import config


def load_tests(test_type):
    test_dir = pathlib.Path(__file__).parent
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

    parser = DucklingPlugin(
        dimensions=["time"], locale="en_IN", timezone="Asia/Kolkata"
    )

    with pytest.raises(ValueError):
        parser._get_entities(body)


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

    parser = DucklingPlugin(
        locale="en_IN", timezone="Earth/Someplace", dimensions=["time"]
    )

    with pytest.raises(pytz.UnknownTimeZoneError):
        _ = parser._get_entities(body)


# == Test transformation of unknown entity type ==
def test_entity_object_not_implemented() -> None:
    """
    Reshape converts json response from Duckling APIs
    to dialogy's BaseEntity.

    We are checking for an unknown entity type here.
    This would lead to a `NotImplementedError`.
    """
    entities_json = [config.mock_unknown_entity]
    parser = DucklingPlugin(
        locale="en_IN", dimensions=["unknown"], timezone="Asia/Kolkata"
    )

    with pytest.raises(NotImplementedError):
        parser._reshape(entities_json)


# == Test missing i/o ==
def test_plugin_io_missing() -> None:
    """
    Here we are checking if the plugin has access to workflow.
    Since we haven't provided `access`, `mutate` to `DucklingPlugin`
    we will receive a `TypeError`.
    """
    parser = DucklingPlugin(
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
    Since we have provided `access`, `mutate` of incorrect types to `DucklingPlugin`
    we will receive a `TypeError`.
    """
    parser = DucklingPlugin(
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


@pytest.mark.parametrize(
    "body",
    [42, None, {"key", 42}, [12]],
)
@httpretty.activate
def test_plugin_type_errors(body) -> None:
    """
    An end-to-end example showing how `DucklingPlugin` works in case
    the input is invalid.
    """

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingPlugin(
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

    parser = DucklingPlugin(
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


@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("asserts"))
def test_plugin_working_cases(payload) -> None:
    """
    An end-to-end example showing how to use `DucklingPlugin` with a `Worflow`.
    """
    body = payload["input"]
    mock_entity_json = payload["mock_entity_json"]
    expected_types = payload["expected"]

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingPlugin(
        access=access,
        mutate=mutate,
        dimensions=["people", "time", "date", "duration"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder(mock_entity_json)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])
    workflow.run(body)
    module = importlib.import_module("dialogy.types.entity")

    if not workflow.output["entities"]:
        assert workflow.output["entities"] == []

    for i, entity in enumerate(workflow.output["entities"]):
        class_name = expected_types[i]["type"]
        assert isinstance(entity, getattr(module, class_name))


@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("exceptions"))
def test_plugin_expected_failures(payload) -> None:
    """
    An end-to-end example showing how to use `DucklingPlugin` with a `Worflow`.
    """
    body = payload["input"]
    mock_entity_json = payload["mock_entity_json"]
    expected_types = payload["expected"]
    exceptions = {"TypeError": TypeError, "KeyError": KeyError}

    def access(workflow):
        return workflow.input, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingPlugin(
        access=access,
        mutate=mutate,
        dimensions=["people", "time", "date", "duration"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    request_callback = request_builder(mock_entity_json)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])
    with pytest.raises(exceptions[expected_types]):
        workflow.run(body)

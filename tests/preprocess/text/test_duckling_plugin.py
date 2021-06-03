import datetime
import importlib

import httpretty
import pytest

from dialogy.preprocess.text.duckling_plugin import DucklingPlugin
from dialogy.types import BaseEntity
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, request_builder


def test_plugin_with_custom_entity_map() -> None:
    """
    Here we are checking if the plugin has access to workflow.
    Since we haven't provided `access`, `mutate` to `DucklingPlugin`
    we will receive a `TypeError`.
    """
    parser = DucklingPlugin(
        locale="en_IN",
        timezone="Asia/Kolkata",
        dimensions=["time"],
        entity_map={"number": {"value": BaseEntity}},
    )
    assert parser.dimension_entity_map["number"]["value"] == BaseEntity


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


@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_plugin_working_cases(payload) -> None:
    """
    An end-to-end example showing how to use `DucklingPlugin` with a `Workflow`.
    """
    body = payload["input"]
    mock_entity_json = payload["mock_entity_json"]
    expected_types = payload.get("expected")
    exception = payload.get("exception")
    duckling_args = payload.get("duckling")
    response_code = payload.get("response_code", 200)
    locale = payload.get("locale")
    reference_time = payload.get("reference_time")

    def access(workflow):
        return workflow.input, reference_time, locale

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    parser = DucklingPlugin(access=access, mutate=mutate, **duckling_args)

    request_callback = request_builder(mock_entity_json, response_code=response_code)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow(preprocessors=[parser()], postprocessors=[])

    if expected_types is not None:
        workflow.run(body)
        module = importlib.import_module("dialogy.types.entity")

        if not workflow.output["entities"]:
            assert workflow.output["entities"] == []

        for i, entity in enumerate(workflow.output["entities"]):
            class_name = expected_types[i]["entity"]
            assert isinstance(entity, getattr(module, class_name))
    else:
        with pytest.raises(EXCEPTIONS[exception]):
            workflow.run(body)

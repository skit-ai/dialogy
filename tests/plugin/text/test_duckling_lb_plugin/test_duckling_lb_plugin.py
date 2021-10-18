import importlib

import httpretty
import pytest

from dialogy.plugins import DucklingPluginLB
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, request_builder


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
    use_latent = payload.get("use_latent")

    def access(workflow):
        return workflow.input, reference_time, locale, use_latent

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    duckling_plugin = DucklingPluginLB(access=access, mutate=mutate, **duckling_args)

    request_callback = request_builder(mock_entity_json, response_code=response_code)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow([duckling_plugin])

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
import importlib

import httpretty
import pytest
import json

from dialogy.base import Input, Output
from dialogy.plugins.registry import DucklingPluginLB
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, MockResponse


@pytest.mark.asyncio
@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
async def test_plugin_working_cases(payload, mocker) -> None:
    """
    An end-to-end example showing how to use `DucklingPlugin` with a `Workflow`.
    """
    inputs = payload["input"]
    if isinstance(inputs, str):
        inputs = [inputs]
    body = [[{"transcript": x} for x in inputs]]
    mock_entity_json = payload["mock_entity_json"]
    expected_types = payload.get("expected")
    exception = payload.get("exception")
    duckling_args = payload.get("duckling")
    response_code = payload.get("response_code", 200)
    locale = payload.get("locale")
    reference_time = payload.get("reference_time")
    use_latent = payload.get("use_latent")

    duckling_plugin = DucklingPluginLB(dest="output.entities", **duckling_args)

    resp = MockResponse(json.dumps(mock_entity_json), response_code)
    mocker.patch('aiohttp.ClientSession.post', return_value=resp)

    workflow = Workflow([duckling_plugin])

    if expected_types is not None:
        _, output = await workflow.run(
            Input(
                utterances=body,
                locale=locale,
                reference_time=reference_time,
                latent_entities=use_latent,
            )
        )
        output = output.dict()

        for i, entity in enumerate(output["entities"]):
            assert entity["entity_type"] == expected_types[i]["entity_type"]
    else:
        with pytest.raises(EXCEPTIONS[exception]):
            await workflow.run(body)

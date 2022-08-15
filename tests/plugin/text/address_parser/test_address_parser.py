import json

import httpretty
import pytest

from dialogy import plugins
from dialogy.base import Input, Output
from dialogy.types import Intent
from dialogy.workflow import Workflow
from dialogy import plugins
from dialogy.types import AddressEntity
from tests import load_tests


@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_address_parser_plugin(payload) -> None:

    input_ = Input(**payload["input"])

    output = Output(
        intents=[
            Intent(
                name=x["name"],
                alternative_index=x["alternative_index"],
                parsers=x["parsers"],
                slots=x["slots"],
            )
            for x in payload["output"]["intents"]
            if payload["output"]["intents"]
        ],
        entities=[AddressEntity.from_dict(x) for x in payload["output"]["entities"]],
    )
    expected = Output(
        intents=[
            Intent(
                name=x["name"],
                alternative_index=x["alternative_index"],
                parsers=x["parsers"],
                slots=x["slots"],
            )
            for x in payload["expected"]["intents"]
        ],
        entities=[AddressEntity.from_dict(x) for x in payload["expected"]["entities"]],
    )

    provider = payload["maps_provider"]
    maps_api_response = payload.get("maps_prediction", "")
    req_status = payload.get("status", 200)

    if provider == "google":
        url = "https://maps.googleapis.com/maps/api/place/autocomplete/json?"
    elif provider == "mmi":
        url = "https://atlas.mapmyindia.com/api/places/geocode?"

    httpretty.register_uri(
        httpretty.GET, url, body=json.dumps(maps_api_response), status=req_status
    )

    address_plugin = plugins.AddressParserPlugin(
        dest="output.entities",
        provider=provider,
        address_capturing_intents="inform_address",
        country_code="IND",
        language="en",
        pincode_capturing_intents="inform_pincode",
        pincode_slot_name="pincode",
    )

    workflow = Workflow([address_plugin])
    workflow.input = input_
    workflow.output = output

    address_plugin(workflow)

    assert expected == workflow.output

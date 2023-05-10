import collections
import json
import requests
from datetime import timedelta

import httpretty
import pytest
import googlemaps

from dialogy.plugins.registry import AddressParserPlugin
from dialogy.base import Input, Output
from dialogy.plugins.text.address_parser import MissingCredentials
from dialogy.plugins.text.address_parser.mapmyindia import MapMyIndia
from dialogy.types import Intent
from dialogy.workflow import Workflow
from dialogy import plugins
from dialogy.types import AddressEntity
from tests import load_tests, MockResponse

_USER_AGENT = "GoogleGeoApiClientPython/%s" % googlemaps.__version__


def fake_mmi_get_token(x) -> str:
    return "fake_token"


def fake_gmaps_client_init(
    self,
    key=None,
    client_id=None,
    client_secret=None,
    timeout=None,
    connect_timeout=None,
    read_timeout=None,
    retry_timeout=60,
    requests_kwargs=None,
    queries_per_second=50,
    channel=None,
    retry_over_query_limit=True,
    experience_id=None,
    requests_session=None,
    base_url="https://maps.googleapis.com",
) -> None:
    if not key and not (client_secret and client_id):
        raise ValueError(
            "Must provide API key or enterprise credentials " "when creating client."
        )
    self.session = requests_session or requests.Session()
    self.key = key

    if timeout and (connect_timeout or read_timeout):
        raise ValueError(
            "Specify either timeout, or connect_timeout " "and read_timeout"
        )

    if connect_timeout and read_timeout:
        # Check that the version of requests is >= 2.4.0
        chunks = requests.__version__.split(".")
        if int(chunks[0]) < 2 or (int(chunks[0]) == 2 and int(chunks[1]) < 4):
            raise NotImplementedError(
                "Connect/Read timeouts require " "requests v2.4.0 or higher"
            )
        self.timeout = (connect_timeout, read_timeout)
    else:
        self.timeout = timeout

    self.client_id = client_id
    self.client_secret = client_secret
    self.channel = channel
    self.retry_timeout = timedelta(seconds=retry_timeout)
    self.requests_kwargs = requests_kwargs or {}
    headers = self.requests_kwargs.pop("headers", {})
    headers.update({"User-Agent": _USER_AGENT})
    self.requests_kwargs.update(
        {
            "headers": headers,
            "timeout": self.timeout,
            "verify": True,  # NOTE(cbro): verify SSL certs.
        }
    )

    self.queries_per_second = queries_per_second
    self.retry_over_query_limit = retry_over_query_limit
    self.sent_times = collections.deque("", queries_per_second)
    self.set_experience_id(experience_id)
    self.base_url = base_url


@httpretty.activate
@pytest.mark.asyncio
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
async def test_address_parser_plugin(payload, monkeypatch, mocker) -> None:

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
        monkeypatch.setattr(googlemaps.Client, "__init__", fake_gmaps_client_init)
        resp = MockResponse(json.dumps(maps_api_response.get("predictions", [])), req_status) \
            if req_status == 200 else None
        mocker.patch('googlemaps.Client.places_autocomplete', return_value=resp)
    elif provider == "mmi":
        url = "https://atlas.mapmyindia.com/api/places/geocode?"
        monkeypatch.setattr(MapMyIndia, "_get_token", fake_mmi_get_token)
        resp = MockResponse(json.dumps(maps_api_response), req_status)
        mocker.patch('dialogy.plugins.text.address_parser.mapmyindia.MapMyIndia.geocode', return_value=resp)

    address_plugin = AddressParserPlugin(
        dest="output.entities",
        provider=provider,
        address_capturing_intents="inform_address",
        gmaps_api_token="fake_token",
        mmi_client_id="fake_client_id",
        mmi_client_secret="fake_client_secret",
        country_code="IND",
        language="en",
        pincode_capturing_intents="inform_pincode",
        pincode_slot_name="pincode",
    )

    workflow = Workflow([address_plugin])

    _, predicted_output = await workflow.run(input_, output)

    assert expected == predicted_output


def test_missing_creds_gmaps() -> None:
    with pytest.raises(MissingCredentials):
        address_plugin = AddressParserPlugin(
            dest="output.entities",
            provider="google",
            address_capturing_intents="inform_address",
            country_code="IND",
            language="en",
            pincode_capturing_intents="inform_pincode",
            pincode_slot_name="pincode",
        )


def test_missing_creds_mmi() -> None:
    with pytest.raises(MissingCredentials):
        address_plugin = AddressParserPlugin(
            dest="output.entities",
            provider="mmi",
            address_capturing_intents="inform_address",
            country_code="IND",
            language="en",
            pincode_capturing_intents="inform_pincode",
            pincode_slot_name="pincode",
        )


def test_mmi_get_token() -> None:
    with pytest.raises(KeyError):
        client = MapMyIndia("fake_client_id", "fake_client_secrets")

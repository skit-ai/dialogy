import importlib
import time

import httpretty
import pandas as pd
import pytest
import requests

from dialogy.plugins import DucklingPlugin
from dialogy.base import Input
from dialogy.utils import make_unix_ts
from dialogy.types import BaseEntity, KeywordEntity, TimeEntity
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, request_builder


def test_plugin_with_custom_entity_map() -> None:
    """
    Here we are checking if the plugin has access to workflow.
    Since we haven't provided `access`, `mutate` to `DucklingPlugin`
    we will receive a `TypeError`.
    """
    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        timezone="Asia/Kolkata",
        dimensions=["time"],
        entity_map={"number": {"value": BaseEntity}},
    )
    assert duckling_plugin.dimension_entity_map["number"]["value"] == BaseEntity


# def test_plugin_io_missing() -> None:
#     """
#     Here we are checking if the plugin has access to workflow.
#     Since we haven't provided `access`, `mutate` to `DucklingPlugin`
#     we will receive a `TypeError`.
#     """
#     duckling_plugin = DucklingPlugin(
#         locale="en_IN", timezone="Asia/Kolkata", dimensions=["time"]
#     )

#     workflow = Workflow([duckling_plugin])
#     with pytest.raises(TypeError):
#         workflow.run("")


# # == Test invalid i/o ==
# @pytest.mark.parametrize(
#     "access,mutate",
#     [
#         (1, 1),
#         (lambda x: x, 1),
#         (1, lambda x: x),
#     ],
# )
# def test_plugin_io_type_mismatch(access, mutate) -> None:
#     """
#     Here we are chcking if the plugin has access to workflow.
#     Since we have provided `access`, `mutate` of incorrect types to `DucklingPlugin`
#     we will receive a `TypeError`.
#     """
#     duckling_plugin = DucklingPlugin(
#         access=access,
#         mutate=mutate,
#         locale="en_IN",
#         dimensions=["time"],
#         timezone="Asia/Kolkata",
#     )

#     workflow = Workflow([duckling_plugin])
#     with pytest.raises(TypeError):
#         workflow.run("")


def test_remove_low_scoring_entities_works_only_if_threshold_is_not_none():
    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
    )

    body = "12th december"

    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="basic",
        dim="default",
        values=[],
        score=0.2,
    )

    assert duckling_plugin.remove_low_scoring_entities([entity]) == [entity]


def test_remove_low_scoring_entities_doesnt_remove_unscored_entities():
    duckling_plugin = DucklingPlugin(
        locale="en_IN", dimensions=["time"], timezone="Asia/Kolkata", threshold=0.2
    )

    body = "12th december"

    entity_A = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="basic",
        dim="default",
        values=[],
        score=0.0
    )
    entity_B = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="basic",
        dim="default",
        values=[],
        score=0.5,
    )

    assert duckling_plugin.remove_low_scoring_entities([entity_A, entity_B]) == [
        entity_B,
    ]


@httpretty.activate
def test_duckling_timeout() -> None:
    """
    [summary]

    :return: [description]
    :rtype: [type]
    """
    locale = "en_IN"
    wait_time = 0.1

    def raise_timeout(_, __, headers):
        time.sleep(wait_time)
        return 200, headers, "received"

    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=raise_timeout
    )

    duckling_plugin = DucklingPlugin(
        locale=locale,
        dimensions=["time"],
        timezone="Asia/Kolkata",
        threshold=0.2,
        timeout=0.01,
        dest="output.entities"
    )


    workflow = Workflow([duckling_plugin])
    _, output = workflow.run(Input(utterances="test"))
    assert output["entities"] == []


def test_duckling_connection_error() -> None:
    """
    [summary]

    :return: [description]
    :rtype: [type]
    """
    locale = "en_IN"

    duckling_plugin = DucklingPlugin(
        locale=locale,
        dimensions=["time"],
        timezone="Asia/Kolkata",
        dest="output.entities",
        threshold=0.2,
        timeout=0.01,
        url="https://duckling/parse",
    )

    workflow = Workflow([duckling_plugin])
    _, output = workflow.run(Input(utterances="test", locale=locale))
    assert output["entities"] == []


def test_max_workers_greater_than_zero() -> None:
    """Checks that "ValueError: max_workers must be greater than 0" is not raised when there are no transcriptions

    When we get an empty transcription from ASR in a production setup, FSM does not send the empty transcription to the SLU service.

    Whereas in a development setup, when one tries to run `slu test` with atleast one data point that does not have any transcriptions(`[]`)
    it will raise a `ValueError: max_workers must be greater than 0` exception.

    The corresponding fix has been done and this test ensures that the exception is not raised when there are no transcriptions even in development setup

    :return: None
    :rtype: None
    """
    locale = "en_IN"

    duckling_plugin = DucklingPlugin(
        dest="output.entities",
        dimensions=["time"],
        timezone="Asia/Kolkata",
        url="https://duckling/parse",
    )

    workflow = Workflow([duckling_plugin])
    alternatives = []  # When ASR returns empty transcriptions.
    try:
        workflow.run(Input(utterances=alternatives, locale=locale))
    except ValueError as exc:
        pytest.fail(f"{exc}")


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

    duckling_plugin = DucklingPlugin(dest="output.entities", **duckling_args)

    request_callback = request_builder(mock_entity_json, response_code=response_code)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    workflow = Workflow([duckling_plugin])
    if isinstance(reference_time, str):
        reference_time = make_unix_ts("Asia/Kolkata")(reference_time)

    if expected_types is not None:
        input_ = Input(utterances=body, locale=locale, reference_time=reference_time, latent_entities=use_latent)
        _, output = workflow.run(input_)

        if not output["entities"]:
            assert output["entities"] == []

        for i, entity in enumerate(output["entities"]):
            expected_entity_type = expected_types[i]["entity_type"]
            assert entity["entity_type"] == expected_entity_type
    else:
        with pytest.raises(EXCEPTIONS[exception]):
            input_ = Input(utterances=body, locale=locale, reference_time=reference_time, latent_entities=use_latent)
            workflow.run(input_)


@httpretty.activate
def test_plugin_no_transform():
    mock_entity_json = [
        {
            "body": "today",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2021-09-14T00:00:00.000+05:30",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-09-14T00:00:00.000+05:30",
                "grain": "day",
                "type": "value",
            },
            "end": 5,
            "dim": "time",
            "latent": False,
        }
    ]
    request_callback = request_builder(mock_entity_json, response_code=200)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    df = pd.DataFrame(
        [
            {
                "data": ["today"],
                "reftime": "2021-09-14T00:00:00.000+05:30",
            },
            {
                "data": ["no"],
                "reftime": "2021-09-14T00:00:00.000+05:30",
            },
        ],
        columns=["data", "reftime"],
    )

    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
        dest="output.entities",
        threshold=0.2,
        timeout=0.01,
        use_transform=False,
        input_column="data",
        output_column="entities",
    )

    df_ = duckling_plugin.transform(df)
    assert "entities" not in df_.columns


@httpretty.activate
def test_plugin_transform():
    mock_entity_json = [
        {
            "body": "today",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2021-09-14T00:00:00.000+05:30",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-09-14T00:00:00.000+05:30",
                "grain": "day",
                "type": "value",
            },
            "end": 5,
            "dim": "time",
            "latent": False,
        }
    ]
    request_callback = request_builder(mock_entity_json, response_code=200)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    df = pd.DataFrame(
        [
            {
                "data": ["today"],
                "reftime": "2021-09-14T00:00:00.000+05:30",
            },
            {
                "data": ["no"],
                "reftime": "2021-09-14T00:00:00.000+05:30",
            },
        ],
        columns=["data", "reftime"],
    )

    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
        dest="output.entities",
        threshold=0.1,
        timeout=0.01,
        use_transform=True,
        input_column="data",
        output_column="entities",
    )

    today = TimeEntity(
        entity_type="date",
        body="today",
        parsers=["DucklingPlugin"],
        range={"start": 0, "end": 5},
        score=1.0,
        alternative_index=0,
        latent=False,
        value="2021-09-14T00:00:00.000+05:30",
        origin="value",
        grain="day",
    )

    df_ = duckling_plugin.transform(df)
    parsed_entity = df_["entities"].iloc[0][0]
    assert parsed_entity.value == today.value
    assert parsed_entity.type == today.type


@httpretty.activate
def test_plugin_transform_type_error():
    mock_entity_json = [
        {
            "body": "today",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2021-09-14T00:00:00.000+05:30",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-09-14T00:00:00.000+05:30",
                "grain": "day",
                "type": "value",
            },
            "end": 5,
            "dim": "time",
            "latent": False,
        }
    ]
    request_callback = request_builder(mock_entity_json, response_code=200)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    df = pd.DataFrame(
        [
            {
                "data": ["no"],
                "reftime": [],
            },
        ],
        columns=["data", "reftime"],
    )

    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
        dest="output.entities",
        threshold=0.2,
        timeout=0.01,
        use_transform=True,
        input_column="data",
        output_column="entities",
    )

    with pytest.raises(TypeError):
        _ = duckling_plugin.transform(df)


@httpretty.activate
def test_plugin_transform_existing_entity():
    mock_entity_json = [
        {
            "body": "today",
            "start": 0,
            "value": {
                "values": [
                    {
                        "value": "2021-09-14T00:00:00.000+05:30",
                        "grain": "day",
                        "type": "value",
                    }
                ],
                "value": "2021-09-14T00:00:00.000+05:30",
                "grain": "day",
                "type": "value",
            },
            "end": 5,
            "dim": "time",
            "latent": False,
        }
    ]
    request_callback = request_builder(mock_entity_json, response_code=200)
    httpretty.register_uri(
        httpretty.POST, "http://0.0.0.0:8000/parse", body=request_callback
    )

    df = pd.DataFrame(
        [
            {
                "data": '["today"]',
                "reftime": "2021-09-14T00:00:00.000+05:30",
            },
            {
                "data": '["no"]',
                "reftime": "2021-09-14T00:00:00.000+05:30",
                "entities": [
                    KeywordEntity(
                        range={"start": 0, "end": 0},
                        value="apple",
                        entity_type="fruits",
                        body="apple",
                    )
                ],
            },
            {
                "data": '["no"]',
                "reftime": pd.NA,
                "entities": [
                    KeywordEntity(
                        range={"start": 0, "end": 0},
                        value="apple",
                        entity_type="fruits",
                        body="apple",
                    )
                ],
            },
        ],
        columns=["data", "reftime", "entities"],
    )

    duckling_plugin = DucklingPlugin(
        locale="en_IN",
        dimensions=["time"],
        timezone="Asia/Kolkata",
        dest="output.entities",
        threshold=0.2,
        timeout=0.01,
        use_transform=True,
        input_column="data",
        output_column="entities",
    )

    df_ = duckling_plugin.transform(df)
    today = TimeEntity(
        entity_type="date",
        body="today",
        parsers=["DucklingPlugin"],
        range={"start": 0, "end": 5},
        score=1.0,
        alternative_index=0,
        latent=False,
        value="2021-09-14T00:00:00.000+05:30",
        origin="value",
        grain="day",
    )
    parsed_entity = df_["entities"].iloc[0][0]
    assert parsed_entity.value == today.value
    assert parsed_entity.type == today.type
    assert df_["entities"].iloc[1][0].value == "apple"

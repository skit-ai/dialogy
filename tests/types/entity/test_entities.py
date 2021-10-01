"""
Tests for entities
"""
import importlib
from datetime import datetime

import httpretty
import pytest

from dialogy.plugins import DucklingPlugin
from dialogy.types.entity import (
    BaseEntity,
    LocationEntity,
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
    entity_synthesis,
)
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, request_builder


class MockPlugin:
    ...


def make_mock_entity():
    return {
        "body": "6pm",
        "start": 0,
        "value": {
            "values": [
                {
                    "value": "2021-01-15T18:00:00.000-08:00",
                    "grain": "hour",
                    "type": "value",
                },
                {
                    "value": "2021-01-16T18:00:00.000-08:00",
                    "grain": "hour",
                    "type": "value",
                },
                {
                    "value": "2021-01-17T18:00:00.000-08:00",
                    "grain": "hour",
                    "type": "value",
                },
            ],
            "value": "2021-01-15T18:00:00.000-08:00",
            "grain": "hour",
            "type": "value",
        },
        "end": 3,
        "dim": "time",
        "latent": False,
    }


def test_entity_parser():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"value": 0}],
    )
    entity.add_parser(MockPlugin())

    assert entity.parsers == ["MockPlugin"], "parser was not added"
    assert entity.get_value() == 0, "value incorrect"


def test_entity_values_index_error():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[],
    )
    with pytest.raises(IndexError):
        entity.get_value()


def test_entity_deep_copy():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="basic",
        dim="default",
        values=[],
    )

    entity_copy = entity.copy()
    entity_copy.body = "12th november"

    # Had this not been a deep copy, it would have matched.
    assert entity_copy.body != entity.body, "Shouldn't be same"


def test_base_entity_value_setter():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="basic",
        dim="default",
        values=[],
    )

    # Had this not been a deep copy, it would have matched.
    assert entity.get_value({"value": 5}) == 5, "Should be same"


def test_entity_synthesis():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[],
    )
    synthetic_entity = entity_synthesis(entity, "body", "12th november")
    assert synthetic_entity.body != entity.body, "Shouldn't be same"


def test_entity_synthesis_exception():
    body = "12th december"
    entity = {}
    with pytest.raises(TypeError):
        entity_synthesis(entity, "body", body)


def test_entity_values_key_error():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
    )
    with pytest.raises(KeyError):
        entity.get_value()


def test_entity_parser_from_dict():
    mock_entity = make_mock_entity()
    BaseEntity.from_dict(mock_entity)


def test_people_entity_unit_not_str_error():
    body = "12 people"
    with pytest.raises(TypeError):
        _ = PeopleEntity(
            range={"from": 0, "to": len(body)}, body=body, type="people", unit=0
        )


def test_time_entity_grain_not_str_error():
    body = "12 pm"
    with pytest.raises(TypeError):
        _ = TimeEntity(
            range={"from": 0, "to": len(body)}, body=body, type="time", grain=0
        )


def test_time_interval_entity_value_not_dict_error():
    body = "from 4 pm to 12 am"
    with pytest.raises(TypeError):
        _ = TimeIntervalEntity(
            range={"from": 0, "to": len(body)}, body=body, type="time", grain=0
        )


def test_location_entity_value_not_int_error():
    body = "bangalore"
    with pytest.raises(TypeError):
        _ = LocationEntity(
            range={"from": 0, "to": len(body)}, body=body, type="location"
        )


def test_entity_set_value_values_present():
    body = "four"
    entity = NumericalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"value": 4}],
    )
    entity.set_value()
    assert entity.value == 4


def test_entity_set_value_values_missing():
    body = "four"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
    )
    entity.set_value(value=4)
    assert entity.value == 4


def test_interval_entity_set_value_values_missing() -> None:
    body = "between 2 to 4 am"
    value = {
        "to": {"value": "2021-01-22T05:00:00.000+05:30", "grain": "hour"},
        "from": {"value": "2021-01-22T02:00:00.000+05:30", "grain": "hour"},
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
    )
    entity.set_value()
    assert entity.value == value


def test_entity_jsonify() -> None:
    body = "12th december"
    value = "value"
    values = [{"key": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=values,
    )
    entity.set_value(value)
    entity_json = entity.json()
    assert "dim" not in entity_json
    assert entity_json.get("value") == value


def test_entity_jsonify_unrestricted() -> None:
    body = "12th december"
    value = "value"
    values = [{"key": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=values,
    )
    entity_json = entity.json(add=["dim", "values"])
    assert entity_json.get("dim") == "default"
    assert entity_json.get("body") == body
    assert entity_json.get("values") == values


def test_entity_jsonify_skip() -> None:
    body = "12th december"
    value = "value"
    values = [{"key": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=values,
    )
    entity_json = entity.json(skip=["values"])
    assert "values" not in entity_json


def test_both_entity_type_attributes_match() -> None:
    body = "4 things"
    value = {"value": 4}
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="base",
        values=[value],
    )
    assert entity.type == entity.entity_type


def test_interval_entity_only_from() -> None:
    body = "from 2 am"
    value = {
        "from": {"value": "2021-01-22T02:00:00.000+05:30", "grain": "hour"},
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
    )
    entity.set_value(value=value)
    assert entity.value == value


def test_interval_entity_only_to() -> None:
    body = "to 4 am"
    value = {
        "to": {"value": "2021-01-22T04:00:00.000+05:30", "grain": "hour"},
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
    )
    entity.set_value(value=value)
    assert entity.value == value


def test_bad_interval_entity_neither_from_nor_to() -> None:
    body = "to 4 am"
    value = {"type": "interval"}
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
    )
    with pytest.raises(KeyError):
        entity.get_value(value)


def test_bad_time_entity_invalid_value() -> None:
    body = "4 am"
    value = {"grain": "hour"}
    entity = TimeEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
    )
    with pytest.raises(KeyError):
        entity.get_value(value)


def test_bad_time_entity_no_value() -> None:
    body = "4 am"
    with pytest.raises(ValueError):
        entity = TimeEntity(
            range={"from": 0, "to": len(body)},
            body=body,
            type="time",
            grain="hour",
            values=[],
        )


def test_time_interval_entity_value_neither_from_nor_to() -> None:
    body = "to 4 am"
    value = {
        "to": {"value": "2021-04-17T04:00:00.000+05:30", "grain": "hour"},
        "type": "interval",
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
        value=value,
    )
    del entity.value["to"]
    with pytest.raises(TypeError):
        entity.set_value(value)


def test_time_interval_entity_get_value() -> None:
    body = "to 4 am"
    value = {
        "to": {"value": "2021-06-03T17:00:00.000+05:30", "grain": "hour"},
        "from": {"value": "2021-06-03T15:00:00.000+05:30", "grain": "hour"},
        "type": "interval",
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
        value=value,
    )
    value = "2021-06-03T15:00:00+05:30"
    assert entity.get_value() == datetime.fromisoformat(value)


def test_time_interval_entity_no_value() -> None:
    body = "to 4 am"
    value = {
        "to": {"value": "2021-04-17T04:00:00.000+05:30", "grain": "hour"},
        "type": "interval",
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
        values=[value],
        value=value,
    )
    entity.values = entity.value
    with pytest.raises(TypeError):
        entity.set_value()


@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_entity_type(payload) -> None:
    """
    Evaluate a set of cases from a file.
    """
    body = payload["input"]
    mock_entity_json = payload["mock_entity_json"]
    expected = payload.get("expected")
    exception = payload.get("exception")

    def access(workflow):
        return workflow.input, None, None

    def mutate(workflow, entities):
        workflow.output = {"entities": entities}

    duckling_plugin = DucklingPlugin(
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

    workflow = Workflow([duckling_plugin])

    if expected:
        workflow.run(body)
        module = importlib.import_module("dialogy.types.entity")

        for i, entity in enumerate(workflow.output["entities"]):
            class_name = expected[i]["entity"]
            assert entity.type == expected[i]["type"]
            assert entity.entity_type == expected[i]["type"]
            assert isinstance(entity, getattr(module, class_name))
    elif exception:
        with pytest.raises(EXCEPTIONS[exception]):
            workflow.run(body)

"""
Tests for entities
"""
import pytest

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


def mock_plugin(_: Workflow) -> None:
    pass


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
    entity.add_parser(mock_plugin)

    assert entity.parsers == ["mock_plugin"], "parser was not added"
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
    mock_entity["range"] = {"start": mock_entity["start"], "end": mock_entity["end"]}
    mock_entity["type"] = "basic"
    del mock_entity["start"]
    del mock_entity["end"]
    mock_entity["values"] = mock_entity["value"]["values"]
    del mock_entity["value"]
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


def test_interval_entity_set_value_values_present() -> None:
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
    )
    entity.set_value(value)
    assert entity.value == value


def test_interval_entity_value_not_dict() -> None:
    body = "between 2 to 4 am"
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
    )
    with pytest.raises(TypeError):
        entity.set_value(4)


def test_interval_entity_value_none() -> None:
    body = "between 2 to 4 am"
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        type="time",
        grain="hour",
    )
    with pytest.raises(TypeError):
        entity.set_value()


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


def test_entity_grain_to_type() -> None:
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
    assert entity.entity_type == "hour"
    assert entity.type == "hour"

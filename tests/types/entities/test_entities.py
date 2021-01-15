"""
Tests for entities
"""
import pytest

from dialogy.types.entities import (
    BaseEntity,
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
    LocationEntity,
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
        values=[],
    )
    with pytest.raises(IndexError):
        entity.get_value()


def test_entity_deep_copy():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
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
        values=[],
    )
    synthetic_entity = entity_synthesis(entity, "body", "12th november")
    assert synthetic_entity.body != entity.body, "Shouldn't be same"


def test_entity_synthesis_exception():
    body = "12th december"
    entity = {}
    with pytest.raises(TypeError):
        entity_synthesis(entity, "body", "12th november")


def test_entity_values_key_error():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        values=[{"key": "value"}],
    )
    with pytest.raises(KeyError):
        entity.get_value()


def test_entity_parser_from_dict():
    mock_entity = make_mock_entity()
    mock_entity["range"] = {"start": mock_entity["start"], "end": mock_entity["end"]}
    del mock_entity["start"]
    del mock_entity["end"]
    mock_entity["values"] = mock_entity["value"]["values"]
    del mock_entity["value"]
    BaseEntity.from_dict(mock_entity)


def test_numerical_entity_type_not_str_error():
    body = "12 december"
    with pytest.raises(TypeError):
        _ = NumericalEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="pattern", type=0
        )


def test_people_entity_unit_not_str_error():
    body = "12 people"
    with pytest.raises(TypeError):
        _ = PeopleEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="people", unit=0
        )


def test_time_entity_grain_not_str_error():
    body = "12 pm"
    with pytest.raises(TypeError):
        _ = TimeEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="time", grain=0
        )


def test_time_interval_entity_value_not_dict_error():
    body = "from 4 pm to 12 am"
    with pytest.raises(TypeError):
        _ = TimeIntervalEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="time", grain=0
        )


def test_location_entity_value_not_int_error():
    body = "bangalore"
    with pytest.raises(TypeError):
        _ = LocationEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="location"
        )

"""
Tests for entities
"""
import pytest

from dialogy.types.entities import (BaseEntity,
                                    NumericalEntity,
                                    PeopleEntity,
                                    DateEntity,
                                    TimeEntity,
                                    DatetimeEntity,
                                    TimeIntervalEntity,
                                    DateIntervalEntity,
                                    DatetimeIntervalEntity,
                                    LocationEntity)
from dialogy.workflow import Workflow

def mock_plugin(_: Workflow) -> None:
    pass

def test_entity_parser():
    body = "12th december"
    entity = BaseEntity(
        range={
            "from": 0,
            "to": len(body)
        },
        body = body,
        entity_type = "pattern",
        value = body
    )
    entity.add_parser(mock_plugin)

    assert entity.parsers == ["mock_plugin"]


def test_numerical_entity_type_not_str_error():
    body = "12 december"
    with pytest.raises(TypeError):
        _ = NumericalEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "pattern",
            value = body,
            type = 0
        )


def test_people_entity_unit_not_str_error():
    body = "12 people"
    with pytest.raises(TypeError):
        _ = PeopleEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "people",
            value = body,
            unit = 0
        )


def test_time_entity_grain_not_str_error():
    body = "12 pm"
    with pytest.raises(TypeError):
        _ = TimeEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "time",
            value = body,
            grain = 0
        )


def test_date_entity_type_not_str_error():
    body = "12 december"
    with pytest.raises(TypeError):
        _ = DateEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "date",
            value = body,
            grain = 0
        )


def test_datetime_entity_grain_not_str_error():
    body = "25 december 12 pm"
    with pytest.raises(TypeError):
        _ = DatetimeEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "datetime",
            value = body,
            grain = 0
        )


def test_time_interval_entity_value_not_dict_error():
    body = "from 4 pm to 12 am"
    with pytest.raises(TypeError):
        _ = TimeIntervalEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "time",
            value = body,
            grain = 0
        )


def test_date_interval_entity_value_not_dict_error():
    body = "from 25 december to 29 december"
    with pytest.raises(TypeError):
        _ = DateIntervalEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "date",
            value = body,
            grain = 0
        )


def test_datetime_interval_entity_value_not_dict_error():
    body = "from 25 december 3 pm to 29 december 6 pm"
    with pytest.raises(TypeError):
        _ = DatetimeIntervalEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "datetime",
            value = body,
            grain = 0
        )


def test_location_entity_value_not_int_error():
    body = "bangalore"
    with pytest.raises(TypeError):
        _ = LocationEntity(
            range={
                "from": 0,
                "to": len(body)
            },
            body = body,
            entity_type = "location",
            value = body
        )



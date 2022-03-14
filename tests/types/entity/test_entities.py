"""
Tests for entities
"""
from ast import Num
from datetime import datetime
from unicodedata import numeric

import httpretty
import pytest

from dialogy.base import Input, Plugin
from dialogy.plugins import DucklingPlugin
from dialogy.types import (
    BaseEntity,
    CreditCardNumberEntity,
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
    entity_synthesis,
)
from dialogy.utils import dt2timestamp
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, request_builder


class MockPlugin(Plugin):
    def utility(self, *args):
        return super().utility(*args)


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
        entity_type="basic",
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
        entity_type="basic",
        values=[],
    )
    with pytest.raises(IndexError):
        entity.get_value()


def test_entity_deep_copy():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        entity_type="basic",
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
        entity_type="basic",
        dim="default",
        values=[{"value": 5}],
    )

    # Had this not been a deep copy, it would have matched.
    assert entity.get_value() == 5, "Should be same"


def test_entity_synthesis():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="basic",
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
    with pytest.raises(KeyError):
        entity = BaseEntity(
            range={"from": 0, "to": len(body)},
            body=body,
            dim="default",
            entity_type="basic",
            values=[{"key": "value"}],
        )
        entity.get_value()


def test_entity_parser_from_dict():
    mock_entity = make_mock_entity()
    TimeEntity.from_duckling(mock_entity, 1)


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


def test_time_entities_with_constraint() -> None:
    req_time = dt2timestamp(datetime.fromisoformat("2022-03-06T12:00:00.000+05:30"))
    no_constraint_time = dt2timestamp(
        datetime.fromisoformat("2022-03-06T00:00:00.000+05:30")
    )
    test_constraints = {
        "time": {"lte": {"hour": 21, "minute": 59}, "gte": {"hour": 7, "minute": 0}}
    }
    not_time_constraints = {
        "date": {
            "start": {"year": 2010, "month": 1, "day": 1},
            "end": {"year": 2020, "month": 1, "day": 1},
        }
    }
    d_multiple = {
        "body": "कल 12:00",
        "start": 0,
        "value": {
            "values": [
                {
                    "value": "2022-03-06T00:00:00.000+05:30",
                    "grain": "minute",
                    "type": "value",
                },
                {
                    "value": "2022-03-06T12:00:00.000+05:30",
                    "grain": "minute",
                    "type": "value",
                },
            ],
            "value": "2022-03-06T00:00:00.000+05:30",
            "grain": "minute",
            "type": "value",
        },
        "end": 8,
        "dim": "time",
        "latent": False,
    }

    time_entity = TimeEntity.from_duckling(d_multiple, 1, test_constraints)
    no_constraint_time_entity = TimeEntity.from_duckling(
        d_multiple, 1, not_time_constraints
    )
    assert req_time == dt2timestamp(time_entity.get_value())
    assert no_constraint_time == dt2timestamp(no_constraint_time_entity.get_value())


def test_time_interval_entity_value_not_dict_error():
    body = "from 4 pm to 12 am"
    with pytest.raises(TypeError):
        _ = TimeIntervalEntity(
            range={"from": 0, "to": len(body)}, body=body, entity_type="time", grain=0
        )


def test_interval_entity_set_value_values_missing() -> None:
    body = "between 2 to 4 am"
    d = {
        "body": "between 2 to 4 am",
        "start": 0,
        "value": {
            "values": [
                {
                    "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-12T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-12T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-13T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-13T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
            ],
            "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
        "end": 17,
        "dim": "time",
        "latent": False,
    }

    entity = TimeIntervalEntity.from_duckling(d, 1)
    assert entity.get_value() == datetime.fromisoformat("2022-02-11T02:00:00.000+05:30")


def test_entity_jsonify() -> None:
    body = "12th december"
    value = "value"
    values = [{"value": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="basic",
        values=values,
    )
    entity_json = entity.json()
    assert "dim" not in entity_json
    assert entity_json.get("value") == value


def test_entity_jsonify_unrestricted() -> None:
    body = "12th december"
    value = "value"
    values = [{"value": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="basic",
        values=values,
    )
    entity_json = entity.json(add=["dim", "values"])
    assert entity_json.get("dim") == "default"
    assert entity_json.get("body") == body
    assert entity_json.get("values") == values


def test_entity_jsonify_skip() -> None:
    body = "12th december"
    value = "value"
    values = [{"value": value}]
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        entity_type="basic",
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
        entity_type="base",
        values=[value],
    )
    assert "base" == entity.entity_type


def test_interval_entity_only_from() -> None:
    body = "from 2 am"
    value = {
        "from": {"value": "2021-01-22T02:00:00.000+05:30", "grain": "hour"},
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        entity_type="time",
        grain="hour",
        values=[value],
    )
    assert entity.get_value() == datetime.fromisoformat("2021-01-22T02:00:00.000+05:30")


def test_interval_entity_only_to() -> None:
    body = "to 4 am"
    value = {
        "to": {"value": "2021-01-22T04:00:00.000+05:30", "grain": "hour"},
    }
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        entity_type="time",
        grain="hour",
        values=[value],
    )
    assert entity.get_value() == datetime.fromisoformat("2021-01-22T04:00:00.000+05:30")


def test_bad_interval_entity_neither_from_nor_to() -> None:
    body = "to 4 am"
    value = {"type": "interval"}
    entity = TimeIntervalEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        entity_type="time",
        grain="hour",
        values=[value],
    )
    with pytest.raises(KeyError):
        entity.get_value()


def test_bad_time_entity_invalid_value() -> None:
    body = "4 am"
    value = {"grain": "hour"}
    with pytest.raises(KeyError):
        TimeEntity(
            range={"from": 0, "to": len(body)},
            body=body,
            entity_type="time",
            grain="hour",
            values=[value],
        )


def test_bad_time_entity_no_value() -> None:
    body = "4 am"
    d = {
        "body": "at 4oclock",
        "start": 0,
        "grain": "hour",
        "end": 10,
        "dim": "time",
        "latent": False,
    }

    with pytest.raises(KeyError):
        TimeEntity.from_duckling(d, 1)


def test_time_interval_entity_value_without_range() -> None:
    body = "to 4 am"
    d = {
        "body": "between 2 to 4 am",
        "value": {
            "values": [
                {
                    "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-12T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-12T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-13T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-13T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
            ],
            "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
        "dim": "time",
        "latent": False,
    }

    with pytest.raises(KeyError):
        TimeIntervalEntity.from_duckling(d, 1)


def test_plastic_currency_set_invalid_value():
    with pytest.raises(TypeError):
        CreditCardNumberEntity(range={"from": 0, "to": 1}, body="", value=None)


def test_plastic_currency_set_no_number():
    with pytest.raises(TypeError):
        CreditCardNumberEntity(range={"from": 0, "to": 1}, body="", issuer="visa")


def test_plastic_currency_set_no_issuer():
    with pytest.raises(TypeError):
        CreditCardNumberEntity(
            range={"from": 0, "to": 1}, body="", value="1234-5678-9012-3456"
        )


def test_plastic_currency_get_value():
    body = "My card number is 4111-1111-1111-1111"
    d = {
        "body": "4111-1111-1111-1111",
        "start": 18,
        "value": {"value": "4111111111111111", "issuer": "visa"},
        "end": 37,
        "dim": "credit-card-number",
        "latent": False,
    }

    entity = CreditCardNumberEntity.from_duckling(d, 1)
    assert entity.get_value() == d["value"]["value"]


def test_numerical_entity_as_time() -> None:
    reference_time = dt2timestamp(
        datetime.fromisoformat("2021-01-22T02:00:00.000+05:30")
    )
    numeric_entity = NumericalEntity(value=4, body="4", range={"start": 0, "end": 1})
    time_entity = TimeEntity(
        body="4",
        range={"start": 0, "end": 1},
        value="2021-01-04T02:00:00.000+05:30",
        grain="hour",
    )

    assert (
        numeric_entity.as_time(reference_time, "Asia/Kolkata").get_value()
        == time_entity.get_value()
    )


def test_numerical_entity_fails_for_invalid_replace() -> None:
    reference_time = dt2timestamp(
        datetime.fromisoformat("2021-01-22T02:00:00.000+05:30")
    )
    numeric_entity = NumericalEntity(value=4, body="4", range={"start": 0, "end": 1})

    with pytest.raises(RuntimeError):
        numeric_entity.as_time(reference_time, "Asia/Kolkata", replace="minute")


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
        entity_type="time",
        grain="hour",
        values=[value],
    )
    value = "2021-06-03T15:00:00+05:30"
    assert entity.get_value() == datetime.fromisoformat(value)


def test_time_interval_generation() -> None:
    d = {
        "body": "between 2 to 4 am",
        "value": {
            "values": [
                {
                    "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-12T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-12T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-02-13T05:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-02-13T02:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
            ],
            "to": {"value": "2022-02-11T05:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-02-11T02:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
        "dim": "time",
        "start": 0,
        "end": 17,
        "latent": False,
    }
    entity = TimeIntervalEntity.from_duckling(d, 1)
    modification = "2022-02-10T00:00:00.000+05:30"
    generated = TimeIntervalEntity.from_dict(
        {"value": {"from": modification, "to": "2022-02-11T05:00:00.000+05:30"}},
        reference=entity,
    )
    assert generated.get_value() == datetime.fromisoformat(modification)


def test_time_interval_entity_no_value() -> None:
    body = "to 4 am"
    d = {
        "body": "between 2 to 4 am",
        "start": 0,
        "type": "interval",
        "end": 17,
        "dim": "time",
        "latent": False,
    }

    with pytest.raises(KeyError):
        TimeIntervalEntity.from_duckling(d, 1)


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

    duckling_plugin = DucklingPlugin(
        dest="output.entities",
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
        _, output = workflow.run(Input(utterances=body))
        entities = output["entities"]
        for i, entity in enumerate(entities):
            assert entity["entity_type"] == expected[i]["entity_type"]
    elif exception:
        with pytest.raises(EXCEPTIONS[exception]):
            workflow.run(Input(utterances=body))

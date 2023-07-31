"""
Tests for entities
"""
import copy
from ast import Num
from datetime import datetime
from unicodedata import numeric
from typing import Optional

import httpretty
import pytest
import json

from pydantic import ValidationError

from dialogy.base import Input, Plugin
from dialogy.plugins.registry import DucklingPlugin
from dialogy.types import (
    BaseEntity,
    CreditCardNumberEntity,
    NumericalEntity,
    PeopleEntity,
    KeywordEntity,
    TimeEntity,
    TimeIntervalEntity,
    entity_synthesis,
    EntityDeserializer
)
from dialogy.types.entity.pincode import PincodeEntity
from dialogy.utils import dt2timestamp
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests, MockResponse


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


def test_time_entities_with_constraint() -> None:
    req_time_A = dt2timestamp(datetime.fromisoformat("2022-03-06T12:00:00.000+05:30"))
    req_time_C = dt2timestamp(datetime.fromisoformat("2022-03-06T00:00:00.000+05:30"))
    test_constraints_A = {
        "time": {"lte": {"hour": 21, "minute": 59}, "gte": {"hour": 7, "minute": 0}}
    }

    test_constraints_B = {
        "time": {"lte": {"hour": 21, "minute": 59}, "gte": {"hour": 13, "minute": 0}}
    }

    test_constraints_C = {
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

    time_entity_A = TimeEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_A
    )
    time_entity_B = TimeEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_B
    )
    time_entity_C = TimeEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_C
    )
    d_values = [
        {
            "value": "2022-03-06T12:00:00.000+05:30",
            "grain": "minute",
            "type": "value",
        }
    ]

    assert req_time_A == dt2timestamp(time_entity_A.get_value())
    assert d_values == time_entity_A.values
    assert len(time_entity_B.values) == 0
    assert req_time_C == dt2timestamp(time_entity_C.get_value())


def test_time_interval_entities_with_constraint() -> None:
    test_constraints_A = {
        "time": {"lte": {"hour": 20, "minute": 59}, "gte": {"hour": 9, "minute": 0}}
    }

    test_constraints_B = {
        "time": {"lte": {"hour": 17, "minute": 59}, "gte": {"hour": 12, "minute": 0}}
    }

    test_constraints_C = {
        "date": {
            "start": {"year": 2010, "month": 1, "day": 1},
            "end": {"year": 2020, "month": 1, "day": 1},
        }
    }

    test_constraints_D = {
        "time": {"lte": {"hour": 23, "minute": 59}, "gte": {"hour": 6, "minute": 0}}
    }

    req_time_A = dt2timestamp(datetime.fromisoformat("2022-04-13T09:00:00.000+05:30"))
    req_time_C = dt2timestamp(datetime.fromisoformat("2022-04-13T06:00:00.000+05:30"))
    req_time_D = dt2timestamp(datetime.fromisoformat("2022-04-13T06:00:00.000+05:30"))
    d_multiple = {
        "body": "६ बजे से 10",
        "start": 0,
        "value": {
            "values": [
                {
                    "to": {"value": "2022-04-13T11:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-04-13T06:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
                {
                    "to": {"value": "2022-04-13T23:00:00.000+05:30", "grain": "hour"},
                    "from": {"value": "2022-04-13T18:00:00.000+05:30", "grain": "hour"},
                    "type": "interval",
                },
            ],
            "to": {"value": "2022-04-13T11:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-04-13T06:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
        "end": 11,
        "dim": "time",
        "latent": False,
    }
    d_values_A = [
        {
            "from": {"grain": "hour", "value": "2022-04-13T09:00:00+05:30"},
            "to": {"grain": "hour", "value": "2022-04-13T11:00:00.000+05:30"},
            "type": "interval",
        },
        {
            "from": {"grain": "hour", "value": "2022-04-13T18:00:00.000+05:30"},
            "type": "interval",
        },
    ]

    d_values_D = [
        {
            "to": {"value": "2022-04-13T11:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-04-13T06:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
        {
            "to": {"value": "2022-04-13T23:00:00.000+05:30", "grain": "hour"},
            "from": {"value": "2022-04-13T18:00:00.000+05:30", "grain": "hour"},
            "type": "interval",
        },
    ]

    time_interval_entity_A = TimeIntervalEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_A
    )
    time_interval_entity_B = TimeIntervalEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_B
    )
    time_interval_entity_C = TimeIntervalEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_C
    )
    time_interval_entity_D = TimeIntervalEntity.from_duckling(
        copy.deepcopy(d_multiple), 1, test_constraints_D
    )

    assert req_time_A == dt2timestamp(time_interval_entity_A.get_value())
    assert time_interval_entity_A.values == d_values_A
    assert len(time_interval_entity_B.values) == 0
    assert req_time_C == dt2timestamp(time_interval_entity_C.get_value())
    assert req_time_D == dt2timestamp(time_interval_entity_D.get_value())
    assert time_interval_entity_D.values == d_values_D


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


def test_entity_dict() -> None:
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
    entity_json = entity.dict()
    assert "dim" in entity_json
    assert entity_json.get("value") == value


def test_entity_dict_include() -> None:
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
    entity_json = entity.dict(include={"dim", "body", "values"})
    assert entity_json.get("dim") == "default"
    assert entity_json.get("body") == body
    assert entity_json.get("values") == values


def test_entity_dict_exclude() -> None:
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
    entity_json = entity.dict(exclude={"values"})
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
    with pytest.raises(ValidationError):
        CreditCardNumberEntity(range={"from": 0, "to": 1}, body="", value=None)


def test_plastic_currency_set_no_number():
    with pytest.raises(ValidationError):
        CreditCardNumberEntity(range={"from": 0, "to": 1}, body="", issuer="visa")


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


def test_time_entity_get_day():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    assert time_entity.day == 22


def test_time_entity_set_month():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    time_entity.month = 12
    assert time_entity.value == "2021-12-22T00:00:00+05:30"


def test_time_entity_set_year():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    time_entity.year = 2022
    assert time_entity.value == "2022-01-22T00:00:00+05:30"


def test_time_entity_set_hour():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    assert time_entity.hour == 0
    time_entity.hour = 12
    assert time_entity.value == "2021-01-22T12:00:00+05:30"


def test_time_entity_set_minute():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    assert time_entity.minute == 0
    time_entity.minute = 30
    assert time_entity.value == "2021-01-22T00:30:00+05:30"


def test_time_entity_set_second():
    time_entity = TimeEntity(
        body="today",
        range={"start": 0, "end": 5},
        value="2021-01-22T00:00:00.000+05:30",
        grain="day",
    )
    assert time_entity.second == 0
    time_entity.second = 30
    assert time_entity.value == "2021-01-22T00:00:30+05:30"


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


@pytest.mark.asyncio
@httpretty.activate
@pytest.mark.parametrize("payload", load_tests("cases", __file__))
async def test_entity_type(payload, mocker) -> None:
    """
    Evaluate a set of cases from a file.
    """
    body = [[{"transcript": payload["input"]}]]
    mock_entity_json = payload["mock_entity_json"]
    expected = payload.get("expected")
    exception = payload.get("exception")

    duckling_plugin = DucklingPlugin(
        dest="output.entities",
        dimensions=["people", "time", "date", "duration"],
        locale="en_IN",
        timezone="Asia/Kolkata",
    )

    resp = MockResponse(json.dumps(mock_entity_json), 200)
    mocker.patch('aiohttp.ClientSession.post', return_value=resp)

    workflow = Workflow([duckling_plugin])

    if expected:
        _, output = await workflow.run(Input(utterances=body))
        output = output.dict()
        entities = output["entities"]
        for i, entity in enumerate(entities):
            assert entity["entity_type"] == expected[i]["entity_type"]
    elif exception:
        with pytest.raises(EXCEPTIONS[exception]):
            await workflow.run(Input(utterances=body))


def test_pincode_entity() -> None:
    entity = PincodeEntity.from_pattern(
        transcript="pincode is 560 038", pincode_string="560 038", alternative_index=0
    )
    assert entity.dim == "pincode"
    assert entity.value == "560038"


def test_custom_entity_deser() -> None:
    # deserializing custom entitiy json dict to keyword entity when custom entity class is not accessible
    custom_entity_json_dict = {
        "dim": "custom",
        "custom_attr": "custom-attr",
        "value": "custom-value",
        "body": "custom-value body",
        "range": {"start": 0, "end": 12},
    }

    ent = EntityDeserializer.deserialize_json(**custom_entity_json_dict)
    assert isinstance(ent, KeywordEntity)
    assert ent.meta["custom_attr"] == custom_entity_json_dict["custom_attr"]

    # deserializing keyword entity json dict to custom entity when custom entity class is accessible
    CUSTOM = "custom"
    @EntityDeserializer.register(CUSTOM)
    class CustomEntity(BaseEntity):
        dim: str = CUSTOM

        custom_attr: Optional[str]

        def __init__(self, **data) -> None:
            super().__init__(**data)

        def set_value(self, custom_attr: str):
            self.custom_attr = custom_attr

    data = ent.dict()
    custom_ent = CustomEntity.from_dict(data)
    assert custom_ent.custom_attr == custom_entity_json_dict["custom_attr"]
    
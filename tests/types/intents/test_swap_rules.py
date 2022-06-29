import pytest

from dialogy.types.intent.swap_rules import Dependants, DependencyOp, SwapRule


def test_eq_swap_rule_from_dict():
    rule = SwapRule.from_dict({
        "depends_on": {
            "entity_types": {
                "eq": ["foo"]
            }
        },
        "rename": "bar"
    })
    assert rule.depends_on.entity_types.eq == ["foo"]
    assert rule.rename == "bar"


def test_in_swap_rule_from_dict():
    rule = SwapRule.from_dict({
        "depends_on": {
            "entity_types": {
                "in_": ["foo"]
            }
        },
        "rename": "bar"
    })
    assert rule.depends_on.entity_types.in_ == {"foo"}
    assert rule.rename == "bar"

def test_swap_rule_from_dict_with_eq_shorthand():
    rule = SwapRule.from_dict({
        "depends_on": {
            "entity_types": "foo"
        },
        "rename": "bar"
    })
    assert rule.depends_on.entity_types.eq == "foo"
    assert rule.rename == "bar"


def test_swap_rule_from_dict_with_dependency_op_object():
    rule = SwapRule.from_dict({
        "depends_on": {
            "entity_types": DependencyOp(eq=["foo"])
        },
        "rename": "bar"
    })
    assert rule.depends_on.entity_types.eq == ["foo"]
    assert rule.rename == "bar"


def test_swap_rule_from_dict_with_dependant_object():
    rule = SwapRule.from_dict({
        "depends_on": Dependants(entity_types=DependencyOp(eq=["foo"])),
        "rename": "bar"
    })
    assert rule.depends_on.entity_types.eq == ["foo"]
    assert rule.rename == "bar"


def test_swap_rule_from_dict_with_nonetype_dependant_object():
    rule = SwapRule.from_dict({
        "depends_on": None,
        "rename": "bar"
    })
    assert rule.depends_on is None
    assert rule.rename == "bar"


def test_swap_rule_config_has_same_dict_repr():
    config = {
        "depends_on": {
            "entity_types": {
                "eq": ["foo"]
            }
        },
        "rename": "bar"
    }
    assert SwapRule.from_dict(config).as_dict() == config


def test_in_swap_rule_config_has_same_dict_repr():
    config = {
        "depends_on": {
            "entity_types": {
                "in_": ["foo"]
            }
        },
        "rename": "bar"
    }
    assert SwapRule.from_dict(config).as_dict() == config


def test_invalid_number_of_operations():
    with pytest.raises(ValueError):
        SwapRule.from_dict({
            "depends_on": {
                "entity_types": {
                    "eq": "foo",
                    "ne": "bar"
                }
            },
            "rename": "bar"
        })


def test_rules():
    rule = SwapRule.from_dict({
        "depends_on": {
            "entity_types": "foo",
            "current_state": {
                "in_": ["state1", "state2"]
            }
        },
        "rename": "bar"
    })
    assert rule.parse({
        "entity_types": "foo",
        "state": "state1"
    }) == True

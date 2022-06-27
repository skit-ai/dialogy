from typing import Any, Dict, Set, Union
import attr


def as_set(value: Any) -> Any:
    if isinstance(value, list):
        return set(value)
    return value


@attr.s
class DependencyOp:
    eq: Union[None, str] = attr.ib(default=None, kw_only=True)
    ne: Union[None, str] = attr.ib(default=None, kw_only=True)
    in_: Union[None, Set[str]] = attr.ib(factory=set, converter=as_set, kw_only=True)
    nin: Union[None, Set[str]] = attr.ib(factory=set, converter=as_set, kw_only=True)
    intersects: Union[None, Set[str]] = attr.ib(factory=set, converter=as_set, kw_only=True)
    operations = {
        'eq': lambda a, b: a == b,
        'ne': lambda a, b: a != b,
        'in_': lambda a, b: a in b,
        'nin': lambda a, b: a not in b,
        'intersects': lambda a, b: a.intersection(b),
    }

    def __attrs_post_init__(self):
        d = attr.asdict(self)
        values = [v for v in d.values() if v]
        if len(values) > 1:
            raise ValueError("Only one operation can be specified.")

    @classmethod
    def from_dict(cls, d: Union[None, str, Dict[str, Any], 'DependencyOp']) -> 'DependencyOp':
        if d is None:
            return None
        elif isinstance(d, cls):
            return d
        elif isinstance(d, str):
            return cls(eq=d)
        return cls(
            eq=d.get("eq"),
            ne=d.get("ne"),
            in_=d.get("in_"),
            nin=d.get("nin"),
            intersects=d.get("intersects"),
        )

    def parse(self, value: Union[str, Set[str]]) -> bool:
        """
        Evaluate the condition using the value.

        We have a condition and comparators for one of the given operations.
        We check if the condition is True using the given value.

        .. ipython:: python

            In [1]: from dialogy.types.intent.swap_rules import DependencyOp

            In [2]: op = DependencyOp(eq="foo")
               ...: op.parse("foo")

            In [4]: op = DependencyOp(nin={"foo", "bar"})
               ...: op.parse("foo")

        :param value: A string to compare against.
        :type value: str
        :return: True if condition passes.
        :rtype: bool
        """
        d: Dict[str, Union[str, Set(str)]] = attr.asdict(self)
        for op_name, cmp in d.items():
            if cmp == "__any__":
                return True
            if cmp:
                return DependencyOp.operations[op_name](as_set(value), cmp)


DependencyType = Union[None, DependencyOp]


@attr.s
class Dependants:
    entity_types: DependencyType = attr.ib(default=None, converter=DependencyOp.from_dict, kw_only=True)
    intent: DependencyType = attr.ib(default=None, converter=DependencyOp.from_dict, kw_only=True)
    previous_intent: DependencyType = attr.ib(default=None, converter=DependencyOp.from_dict, kw_only=True)
    state: DependencyType = attr.ib(default=None, converter=DependencyOp.from_dict, kw_only=True)

    @classmethod
    def from_dict(cls, d: Union[None, Dict[str, Any], 'Dependants']) -> 'Dependants':
        if d is None:
            return None
        elif isinstance(d, cls):
            return d
        return cls(
            entity_types=d.get("entity_types"),
            intent=d.get("intent"),
            previous_intent=d.get("previous_intent"),
            state=d.get("state")
        )

    def parse(self, values: Dict[str, Any]) -> bool:
        """
        Evaluate if all conditions pass.

        .. ipython:: python

            In [1]: from dialogy.types.intent.swap_rules import Dependants

            In [2]: dep = Dependants(entity_types={"in_": ["foo", "baz"]}, intent={"eq": "bar"})

            In [3]: dep.parse({"entity_types": "foo"})

            In [4]: dep.parse({"entity_types": "foo", "intent": "bar"})


        We try to check if every dependency that has been specified with a condition,
        evaluates to :code:`True`.

        :param values: A dictionary with keys same as attributes of this object.
        :type values: Dict[str, Any]
        :return: True if all the conditions pass.
        :rtype: bool
        """
        d = attr.asdict(self, recurse=False)
        return all(d[name].parse(value) for name, value in values.items() if d[name])


def exclude_none_values(_: attr.Attribute, value: Any) -> Dict[str, Any]:
    return value is not None


def non_empty_string(_, attr, value):
    return value and isinstance(value, str)


@attr.s
class SwapRule:
    depends_on: Dependants = attr.ib(kw_only=True, converter=Dependants.from_dict)
    rename: str = attr.ib(kw_only=True, validator=non_empty_string)

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'SwapRule':
        return cls(**config)

    def as_dict(self) -> Dict[str, Any]:
        return attr.asdict(self, filter=exclude_none_values)

    def parse(self, values: Dict[str, Any]) -> bool:
        """
        Evaluate if all conditions pass.

        .. ipython:: python

            In [1]: from dialogy.types.intent.swap_rules import SwapRule

            In [2]: rule = SwapRule(depends_on={"entity_types": {"in_": ["foo", "baz"]}, "intent": {"eq": "bar"}}, rename="bar")

            In [3]: rule.parse({"entity_types": "foo"})

            In [4]: rule.parse({"entity_types": "foo", "intent": "bar"})

        :param values: A dictionary with keys same as attributes of this object.
        :type values: Dict[str, Any]
        :return: True if all the conditions pass.
        :rtype: bool
        """
        return self.depends_on.parse(values)

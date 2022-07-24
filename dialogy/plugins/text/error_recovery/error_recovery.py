import calendar
from datetime import timedelta
from typing import Any, Dict, List, Set, Union, Callable, Iterable, Optional

import attr

from dialogy.base import Input, Output, Plugin, Guard
from dialogy.types import BaseEntity, Intent, TimeEntity


TRemove = Optional[str]
TUpdate = Optional[Dict[str, Any]]


@attr.s
class Environment:
    intents: List[Intent] = attr.ib(kw_only=True)
    entities: List[BaseEntity] = attr.ib(kw_only=True)
    previous_intent: Optional[str] = attr.ib(kw_only=True, default=None)
    current_state: Optional[str] = attr.ib(kw_only=True, default=None)
    expected_slots: Set[str] = attr.ib(kw_only=True, factory=set)
    bindings: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    resources = {"intents", "entities"}
    iterables = {"intent", "entity"}

    @property
    def predicted_intent(self) -> str:
        return self.intents[0].name

    def last_day_of_month(self, item: TimeEntity) -> int:
        _, last = calendar.monthrange(item.year, item.month)
        return last

    def last_day_of_week(self, item: TimeEntity) -> int:
        dt = item.get_value()
        weekday = dt.weekday()
        weekend = dt - timedelta(days=weekday) + timedelta(days=6)
        return weekend.day

    def get(self, item: Union[Intent, BaseEntity], key: str) -> Any:
        if "." in key:
            obj, attribute = key.split(".")
            if obj in Environment.iterables:
                return getattr(item, attribute)
        return getattr(self, key)

    def set(self, key: str, value: List[Union[Intent, BaseEntity]]) -> None:
        if key in Environment.resources:
            return setattr(self, key, value)

    def set_item(self, item: Union[Intent, BaseEntity], key: str, value: Any) -> None:
        obj, attribute = key.split(".")
        if value.startswith(":"):
            value = self.get(item, value[1:])
        if obj in Environment.iterables:
            value = value(item) if callable(value) else value
            setattr(item, attribute, value)

@attr.s
class BinaryCondition:
    variable: str = attr.ib(kw_only=True)
    value: Union[str, Set[str]] = attr.ib(kw_only=True)
    operator: Callable[[Any, Any], bool] = attr.ib(kw_only=True)
    operations = {
        'eq': lambda a, b: a == b,
        'ne': lambda a, b: a != b,
        'in': lambda a, b: a in b,
        'nin': lambda a, b: a not in b,
        'gt': lambda a, b: a > b,
        'gte': lambda a, b: a >= b,
        'lt': lambda a, b: a < b,
        'lte': lambda a, b: a <= b,
    }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'BinaryCondition':
        default_op_name = "eq"

        var_name = list(d.keys()).pop()
        op_name = (list(d[var_name].keys()).pop()
            if isinstance(d[var_name], dict)
            else default_op_name)

        value = d[var_name][op_name] if isinstance(d[var_name], dict) else d[var_name]
        if isinstance(value, list):
            value = set(value)

        return cls(
            variable=var_name,
            operator=BinaryCondition.operations[op_name],
            value=value
        )

    @classmethod
    def from_list(cls, d: List[Dict[str, Any]]) -> List['BinaryCondition']:
        return [cls.from_dict(c) for c in d]

@attr.s
class Rule:
    find: str = attr.ib(kw_only=True)
    where: List[BinaryCondition] = attr.ib(converter=BinaryCondition.from_list, kw_only=True) # type: ignore
    remove: TRemove = attr.ib(kw_only=True)
    update: TUpdate = attr.ib(kw_only=True)

    def on_conditions(self, environment: Environment) -> Callable[[Union[Intent, BaseEntity]], bool]:
        conditions = self.where
        def foreach(item: Union[Intent, BaseEntity]) -> bool:
            return all(
                condition.operator(
                    environment.get(item, condition.variable),
                    condition.value
                )
                for condition in conditions
            )
        return foreach

    def on_inverse(self, environment: Environment) -> Callable[[Union[Intent, BaseEntity]], bool]:
        conditions = self.where
        def foreach(item: Union[Intent, BaseEntity]) -> bool:
            return not all(
                condition.operator(
                    environment.get(item, condition.variable),
                    condition.value
                )
                for condition in conditions
            )
        return foreach

    def _find(
        self,
        resource: str,
        clause: Callable[[Union[Intent, BaseEntity]], bool],
        environment: Environment
    ) -> Iterable[Union[Intent, BaseEntity]]:
        resources = (environment.intents
            if resource == "intents"
            else environment.entities)
        return filter(clause, resources) # type: ignore

    def _remove(self, environment: Environment) -> 'Rule':
        if not self.remove:
            return self # pragma: no cover
        resource_name = self.remove
        resources = self._find(resource_name, self.on_inverse(environment), environment)
        if resource_name in Environment.resources:
            environment.set(self.remove, list(resources))
        return self

    def _transform(self, environment: Environment) -> Callable[[Union[Intent, BaseEntity]], Union[Intent, BaseEntity]]:
        def foreach(item: Union[Intent, BaseEntity]) -> Union[Intent, BaseEntity]:
            if not self.update:
                return item # pragma: no cover
            for key, value in self.update.items():
                environment.set_item(item, key, value)
            return item
        return foreach

    def _update(self, environment: Environment) -> 'Rule':
        resource_name = self.find
        resources = self._find(resource_name, self.on_conditions(environment), environment)
        resources = map(self._transform(environment), resources)
        if resource_name in Environment.resources:
            environment.set(self.find, list(resources))
        return self

    def parse(self, environment: Environment) -> 'Rule':
        if self.remove:
            return self._remove(environment)
        if self.update:
            return self._update(environment)
        return self # pragma: no cover

    @classmethod
    def from_dict(cls, rule: Dict[str, Any]) -> 'Rule':
        return cls(
            find=str(rule.get("find")),
            where=rule.get("where"),
            remove=rule.get("remove"),
            update=rule.get("update"),
        )

    @classmethod
    def from_list(
        cls,
        rules: List[Dict[str, Any]]) -> List['Rule']:
        return [cls.from_dict(rule) for rule in rules]


class ErrorRecoveryPlugin(Plugin):
    def __init__(
        self,
        rules: List[Dict[str, Any]],
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        replace_output: bool = True,
        debug: bool = False,
    ) -> None:
        self.rules = Rule.from_list(rules)
        self.dest = dest
        self.guards = guards or []
        self.replace_output = replace_output
        self.debug = debug

    def utility(self, input_: Input, output: Output) -> None:
        environment = Environment(
            intents=output.intents,
            entities=output.entities,
            previous_intent=input_.previous_intent,
            current_state=input_.current_state,
            expected_slots=input_.expected_slots or set(),
        )
        for rule in self.rules:
            rule.parse(environment)

        object.__setattr__(output, "intents", environment.intents)
        object.__setattr__(output, "entities", environment.entities)

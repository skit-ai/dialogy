"""
.. _ErrorRecovery:

The goal of this module is to enable:

#. Richer transitions. Most of our transtions are expressed by maps, we don't have a way to express transitions as a function over known variables. 
#. We have :code:`triggers` that map to the next :code:`state` in the conversation.
#. :code:`triggers` are :code:`intents` in most cases. 
#. ML components produce confidence scores for a prediction. Only in cases of low confidence, should we opt for explicit confirmation.
#. As per our current capabilities, we always have a prompt to confirm.
#. Here the rule for transition is :code:`(intent, score) -> state` instead of :code:`{intent: state}`.
#. Handling ambiguity at the interface. We don't have an expression to implement "Did you mean X or Y" for resolving ambiguities. We have such prompts for certain deployment yet the effort is the same for enabling such for entities other than X, Y and repeats for every deployment.
#. Conversation level defaults. In the above example, we can should be able to define conversation level defaults for certain entities.
#. Personalization. We don't have provisions for handling user information. We have seen cases where speaker's information has to be passed around microservices and the API design is driven by urgency. Does this speaker like when the prompts are faster? slower? shorter? longer? While such information is not logged, we also don't have a way to use it.

These requirements are met by a mature, feature-rich, battle-tested high level language. A language that must expose little noise to its users and offer strong guaranatees of reproducibility, safety and consistency. Building such a language would span work over quarters with dedicated bandwidth of an experienced engineer. Hence we will drop a lot of responsibilities to draft a version that does much less but promises to extend itself to offer coverage of the aforementioned features.

- The language should be approachable for existing engineers in the solutions team.
- It should take a few hours (< 3) to get productive. 
- We will implement rich transitions and conversation level defaults.
"""
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
    """
    The scope of variables for error-recovery rules are defined by this class.
    Referencing SLU input and output variables for filtering and updates.
    """

    intents: List[Intent] = attr.ib(kw_only=True)
    """
    Refer to :ref:`Intent<Intent>`

    Contains the list of intents predicted expected in sorted order of confidence score. 
    Iterable field, can also be modified by update queries.
    """

    entities: List[BaseEntity] = attr.ib(kw_only=True)
    """
    Refer to :ref:`BaseEntity<BaseEntity>`
    Contains a list of entities of varying types.
    Iterable field, can also be modified by update queries.
    """

    previous_intent: Optional[str] = attr.ib(kw_only=True, default=None)
    """
    Read only; used to filter intents/entities if a condition is met. :ref:`Read More<Input>`
    """

    current_state: Optional[str] = attr.ib(kw_only=True, default=None)
    """
    Read only; used to filter intents/entities if a condition is met. :ref:`Read More<Input>`
    """

    expected_slots: Set[str] = attr.ib(kw_only=True, factory=set)
    """
    Read only; used to filter intents/entities if a condition is met. :ref:`Read More<Input>`
    """

    bindings: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    """
    Sub-commands and other variables should be stored here. API is WIP.
    """
    resources = {"intents", "entities"}
    iterables = {"intent", "entity"}

    @property
    def predicted_intent(self) -> str:
        """
        We are assuming intents would be sorted in descending order of confidence scores.
        Hence the first element is the predicted intent as it has the best score.
        """
        return self.intents[0].name

    def last_day_of_month(self, item: TimeEntity) -> int:
        """
        Returns the last day of the month for the given TimeEntity.

        :param item: A time entity.
        :type item: TimeEntity
        :return: The last day of the month
        :rtype: int
        """
        _, last = calendar.monthrange(item.year, item.month)
        return last

    def last_day_of_week(self, item: TimeEntity) -> int:
        """
        Returns the last day of the week for the given TimeEntity.

        :param item: A time entity.
        :type item: TimeEntity
        :return: The last day of the week.
        :rtype: int
        """
        dt = item.get_value()
        weekday = dt.weekday()
        weekend = dt - timedelta(days=weekday) + timedelta(days=6)
        return weekend.day

    def get(self, item: Union[Intent, BaseEntity], key: str) -> Any:
        """
        Seek a variable from the context set in the environment.

        :param item: Either an intent or entity.
        :type item: Union[Intent, BaseEntity]
        :param key: A property within the item or environment.
        :type key: str
        :return: The value bound to the key.
        :rtype: Any
        """
        if "." in key:
            obj, attribute = key.split(".")
            if obj in Environment.iterables:
                return getattr(item, attribute)
        return getattr(self, key)

    def set(self, key: str, value: List[Union[Intent, BaseEntity]]) -> None:
        """
        Bind a value to a variable in the environment.

        :param key: A variable name defined in the environment.
        :type key: str
        :param value: The value to bound to the variable.
        :type value: List[Union[Intent, BaseEntity]]
        :return: None
        :rtype: None
        """
        if key in Environment.resources:
            return setattr(self, key, value)

    def set_item(self, item: Union[Intent, BaseEntity], key: str, value: Any) -> None:
        """
        Bind a value to either Intent or Entity.

        :param item: Either an intent or entity.
        :type item: Union[Intent, BaseEntity]
        :param key: A property within the item.
        :type key: str
        :param value: The value to bound to the property or a function identifier.
        :type value: Any
        """
        obj, attribute = key.split(".")
        if value.startswith(":"):
            value = self.get(item, value[1:])
        if obj in Environment.iterables:
            value = value(item) if callable(value) else value
            setattr(item, attribute, value)


@attr.s
class BinaryCondition:
    """
    This class encodes conditions between two operands.

    Currently supported operators are:

    - :code:`eq` Equality
    - :code:`ne` Non-equality
    - :code:`gte` Greater than
    - :code:`ge` Greater than or equal to
    - :code:`lte` Less than
    - :code:`le` Less than or equal to
    - :code:`in` Inclusion
    - :code:`nin` Exclusion

    :return: _description_
    :rtype: _type_
    """

    variable: str = attr.ib(kw_only=True)
    value: Union[str, Set[str]] = attr.ib(kw_only=True)
    operator: Callable[[Any, Any], bool] = attr.ib(kw_only=True)
    operations = {
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
        "in": lambda a, b: a in b,
        "nin": lambda a, b: a not in b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
    }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "BinaryCondition":
        default_op_name = "eq"

        var_name = list(d.keys()).pop()
        op_name = (
            list(d[var_name].keys()).pop()
            if isinstance(d[var_name], dict)
            else default_op_name
        )

        value = d[var_name][op_name] if isinstance(d[var_name], dict) else d[var_name]
        if isinstance(value, list):
            value = set(value)

        return cls(
            variable=var_name, operator=BinaryCondition.operations[op_name], value=value
        )

    @classmethod
    def from_list(cls, d: List[Dict[str, Any]]) -> List["BinaryCondition"]:
        return [cls.from_dict(c) for c in d]


@attr.s
class Rule:
    """
    We encode events within a conversation turn as a rule.

    A rule can be broken down to 2 operations:

    1. Search: We apply filters to a resource (one of intents or entities).
    2. Action: We perform an action on the resource (one of update, remove).
    """

    find: str = attr.ib(kw_only=True)
    where: List[BinaryCondition] = attr.ib(converter=BinaryCondition.from_list, kw_only=True)  # type: ignore
    remove: TRemove = attr.ib(kw_only=True)
    update: TUpdate = attr.ib(kw_only=True)

    def on_conditions(
        self, environment: Environment
    ) -> Callable[[Union[Intent, BaseEntity]], bool]:
        """
        Pick items within resources when all conditions match.

        We require this to update a set of items that match the conditions.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :return: A function that can be used to filter a resource.
        :rtype: Callable[[Union[Intent, BaseEntity]], bool]
        """
        conditions = self.where

        def foreach(item: Union[Intent, BaseEntity]) -> bool:
            return all(
                condition.operator(
                    environment.get(item, condition.variable), condition.value
                )
                for condition in conditions
            )

        return foreach

    def on_inverse(
        self, environment: Environment
    ) -> Callable[[Union[Intent, BaseEntity]], bool]:
        """
        Pick items within resources when no conditions match.

        We require this to retain a set of items that don't match the conditions.
        That is the remove operation.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :return: A function that can be used to filter a resource.
        :rtype: Callable[[Union[Intent, BaseEntity]], bool]
        """
        conditions = self.where

        def foreach(item: Union[Intent, BaseEntity]) -> bool:
            return not all(
                condition.operator(
                    environment.get(item, condition.variable), condition.value
                )
                for condition in conditions
            )

        return foreach

    def _find(
        self,
        resource: str,
        clause: Callable[[Union[Intent, BaseEntity]], bool],
        environment: Environment,
    ) -> Iterable[Union[Intent, BaseEntity]]:
        """
        Find items within a resource that match a condition.

        :param resource: One of "intents" or "entities".
        :type resource: str
        :param clause: A function that can be used to filter a resource.
        :type clause: Callable[[Union[Intent, BaseEntity]], bool]
        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :return: An iterable of resources filtered by the clause.
        :rtype: Iterable[Union[Intent, BaseEntity]]
        """
        resources = (
            environment.intents if resource == "intents" else environment.entities
        )
        return filter(clause, resources)  # type: ignore

    def _remove(self, environment: Environment) -> "Rule":
        """
        Remove items within a resource that match a condition.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :rtype: Rule
        """
        if not self.remove:
            return self  # pragma: no cover
        resource_name = self.remove
        resources = list(
            self._find(resource_name, self.on_inverse(environment), environment)
        )
        if resource_name in Environment.resources and resources:
            environment.set(self.remove, resources)
        return self

    def _transform(
        self, environment: Environment
    ) -> Callable[[Union[Intent, BaseEntity]], Union[Intent, BaseEntity]]:
        """
        Transform items within a resource as per update rules.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :return: A function that can be used to transform a resource.
        :rtype: Callable[[Union[Intent, BaseEntity]], Union[Intent, BaseEntity]]
        """

        def foreach(item: Union[Intent, BaseEntity]) -> Union[Intent, BaseEntity]:
            if not self.update:
                return item  # pragma: no cover
            for key, value in self.update.items():
                environment.set_item(item, key, value)
            return item

        return foreach

    def _update(self, environment: Environment) -> "Rule":
        """
        Update items within a resource as per update rules.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :rtype: Rule
        """
        resource_name = self.find
        resources = self._find(
            resource_name, self.on_conditions(environment), environment
        )
        resources = list(map(self._transform(environment), resources))
        if resource_name in Environment.resources and resources:
            environment.set(self.find, resources)
        return self

    def parse(self, environment: Environment) -> "Rule":
        """
        Parse a rule and update the environment.

        We parse the rule and either update or remove items within intents or entities as per
        the clause described in the rule.

        :param environment: A data-structure that describes a set of bound variables.
        :type environment: Environment
        :return: Remove or Update resources.
        :rtype: Rule
        """
        if self.remove:
            return self._remove(environment)
        if self.update:
            return self._update(environment)
        return self  # pragma: no cover

    @classmethod
    def from_dict(cls, rule: Dict[str, Any]) -> "Rule":
        return cls(
            find=str(rule.get("find")),
            where=rule.get("where"),
            remove=rule.get("remove"),
            update=rule.get("update"),
        )

    @classmethod
    def from_list(cls, rules: List[Dict[str, Any]]) -> List["Rule"]:
        return [cls.from_dict(rule) for rule in rules]


class ErrorRecoveryPlugin(Plugin):
    """

    .. code-block:: yaml

          rules:
            -
                find: entities
                where:
                    - entity.grain: month
                    - entity.entity_type:
                        in: ["date", "time", "datetime"]
                update:
                    entity.day: :last_day_of_month

    We can use the above rule like so:

    .. ipython::

        In [1]: import yaml
           ...: from dialogy.plugins import ErrorRecoveryPlugin, DucklingPlugin
           ...: from dialogy.workflow import Workflow
           ...: from dialogy.base import Input
           ...: from dialogy.types import Intent

        In [2]: error_recovery_config = yaml.safe_load('''
           ...:   rules:
           ...:     -
           ...:         find: entities
           ...:         where:
           ...:             - entity.grain: month
           ...:             - entity.entity_type:
           ...:                 in: ["date", "time", "datetime"]
           ...:             - predicted_intent: "future_date"
           ...:         update:
           ...:             entity.day: :last_day_of_month
           ...: ''')

        In [3]: duckling_plugin = DucklingPlugin(dimensions=["time"], dest="output.entities")
           ...: workflow = Workflow([duckling_plugin])
           ...: workflow.set("output.intents", [Intent(name="future_date", score=0.99)])
           ...: _, out = workflow.run(input_=Input(utterances="this month"))
           ...: # The default value is 1st of the month
           ...: out["entities"][0]

        In [4]: error_recovery_plugin = ErrorRecoveryPlugin(rules=error_recovery_config["rules"])
           ...: duckling_plugin = DucklingPlugin(dimensions=["time"], dest="output.entities")
           ...: workflow = Workflow([duckling_plugin, error_recovery_plugin])
           ...: workflow.set("output.intents", [Intent(name="future_date", score=0.99)])
           ...: _, out = workflow.run(input_=Input(utterances="this month"))
           ...: # But with error recovery, we get the last day of the month
           ...: out["entities"][0]

        In [5]: error_recovery_config = yaml.safe_load('''
           ...:   rules:
           ...:     -
           ...:         find: entities
           ...:         where:
           ...:             - entity.grain: month
           ...:             - entity.entity_type:
           ...:                 in: ["date", "time", "datetime"]
           ...:             - predicted_intent: "some-other-intent" # Hence the rule won't match
           ...:         update:
           ...:             entity.day: :last_day_of_month
           ...: ''')

        In [6]: error_recovery_plugin = ErrorRecoveryPlugin(rules=error_recovery_config["rules"])
           ...: duckling_plugin = DucklingPlugin(dimensions=["time"], dest="output.entities")
           ...: workflow = Workflow([duckling_plugin, error_recovery_plugin])
           ...: workflow.set("output.intents", [Intent(name="future_date", score=0.99)])
           ...: _, out = workflow.run(input_=Input(utterances="this month"))
           ...: # Only if the conditions are satisfactory.
           ...: out["entities"][0]

    To migrate from the previous intent renaming plugin, here's an example config:

    .. code-block:: yaml

        intent_swap:
        -
            depends_on:
                intent: _confirm_
                state:
                    in:
                        - CONFIRM_VIEWING_POST_HR
                        - CONFIRM_VIEWING_POST_ACCOUNT_RESUMPTION
                        - CONFIRM_VIEWING_POST_ACCOUNT_ACTIVATION
                        - CONFIRM_VIEWING_POST_ASSET_RESUMPTION
                        - CONFIRM_VIEWING_POST_INPUT_CHECK
                        - CONFIRM_VIEWING_POST_RECONNECTION
        rename: _issue_resolved_

    You would express this as:

    .. code-block:: yaml

        rules:
            -
                find: intents
                where:
                - intent.name: _confirm_
                - state:
                    in:
                    - CONFIRM_VIEWING_POST_HR
                    - CONFIRM_VIEWING_POST_ACCOUNT_RESUMPTION
                    - CONFIRM_VIEWING_POST_ACCOUNT_ACTIVATION
                    - CONFIRM_VIEWING_POST_ASSET_RESUMPTION
                    - CONFIRM_VIEWING_POST_INPUT_CHECK
                    - CONFIRM_VIEWING_POST_RECONNECTION
                update:
                    intent.name: _issue_resolved_
    """

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

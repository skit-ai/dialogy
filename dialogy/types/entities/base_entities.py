"""
Base Entity Type
"""
from typing import Any, Callable, Dict, List, Optional

import attr

from dialogy.types.plugins import PluginFn


@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
    Do not use it directly in any preprocessing or postprocessing functions.
    Using it for defining types falls under the intended purposes.

    Keys are:
    - `range` is the character range in the alternative where the entity is parsed
    - `body` is the string that is extracted
    - `entity_type` is the type of the entity
    - `value` is the normalized value of the entity. This can either be a string, an integer or a Dict
    - `parsers` gives the list of all the functions that have changed this entity.
        This list will be in sorted order, which means that the first element has worked
        on the entity first.
    - `score` is the confidence that the range is the entity
    - `alternative_index` is the index of transcript within the ASR output: `List[Utterances]`
        from which this entity was picked up. This may be None.
    """
    range = attr.ib(type=Dict[str, int])
    body = attr.ib(type=str, validator=attr.validators.instance_of(str))
    entity_type = attr.ib(type=str, validator=attr.validators.instance_of(str))
    value = attr.ib(type=Any)
    parsers = attr.ib(type=List[str], default=attr.Factory(list), validator=attr.validators.instance_of(list))
    score = attr.ib(type=Optional[float], default=None)
    alternative_index = attr.ib(type=Optional[int], default=None)

    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an entity. This helps in debugging and has no production utility

        Args:
            postprocessor (PluginFn): Plugin function applied to an entity
        """
        self.parsers.append(postprocessor.__name__)

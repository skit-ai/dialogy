"""
Entity Type
"""

from typing import Any, Callable, Dict, List, Optional

import attr

from dialogy.types.plugins import PluginFn


@attr.s
class BaseEntity:
    """
    Base Entity Type.

    This class is meant for subclassing.
    Do not use it directly.
    """
    range = attr.ib(type=Dict[str, int])
    score = attr.ib(type=float)
    body = attr.ib(type=str)
    entity_type = attr.ib(type=str)
    value = attr.ib(type=str)
    grain = attr.ib(type=str)
    type = attr.ib(type=str)
    unit = attr.ib(type=str)
    parsers = attr.ib(type=List[str], default=attr.Factory(list))
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

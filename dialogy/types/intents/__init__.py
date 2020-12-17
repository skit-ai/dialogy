"""
Intent Type
"""

from typing import Any, Callable, Dict, List, Optional

import attr

from dialogy.types.slots import Slot
from dialogy.types.plugins import PluginFn


@attr.s
class Intent:
    """
    Intent Type    
    """
    name = attr.ib(type=str)
    score = attr.ib(type=float)
    type = attr.ib(type=str, default='main')
    parsers = attr.ib(type=List[str], default=attr.Factory(list))
    alternative_index = attr.ib(type=Optional[int], default=None)
    range = attr.ib(type=Dict[str, int], default=None)
    slots = attr.ib(type=List[Slot], default=attr.Factory(list))

    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an intent. This helps in debugging and has no production utility
        """
        self.parsers.append(postprocessor.__name__)


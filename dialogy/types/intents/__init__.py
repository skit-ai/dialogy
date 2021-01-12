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

    Keys are:
    - `name` is the name of the intent to be used.
    - `score` is the probability of this intent being present in the utterance.
    - `type` is the type of the intent. Intent type can be "main" or "special".
        Intents predicted by a model have type "main" and everything else has "special".
        Any modification to a "main" intent makes it a "special" intent.
    - `parsers` gives the list of all the functions that have changed this intent.
        This list will be in sorted order, which means that the first element has worked
        on the intent first.
    - `alternative_index` is the index of transcript within the ASR output: `List[Utterances]`
        from which this intent was picked up. This may be None if the model uses all the utterances
        to make the prediction.
    - `slots` are the slots associated with this intent.
    """

    name = attr.ib(type=str)
    score = attr.ib(type=float)
    type = attr.ib(type=str, default="main")
    parsers = attr.ib(type=List[str], default=attr.Factory(list))
    alternative_index = attr.ib(type=Optional[int], default=None)
    slots = attr.ib(type=List[Slot], default=attr.Factory(list))

    def add_parser(self, postprocessor: PluginFn) -> None:
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an intent. This helps in debugging and has no production utility
        """
        self.parsers.append(postprocessor.__name__)

"""
This module provides utilities to handle multiple intents from each
alternative from the ASR.
"""
from typing import List

import attr
import numpy as np  # type: ignore
import pydash as py_  # type: ignore

from dialogy import constants as const
from dialogy.plugin import Plugin
from dialogy.types import Signal
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.utils.logger import change_log_level, log
from dialogy.workflow import Workflow


def adjust_signal_strength(signals: List[Signal], trials: int) -> List[Signal]:
    """
    Re-evaluate signal strength.

    Re-evaluation is based on frequency of occurrence and strength of each occurrence,
    normalized by trials.

    Here trials are total attempts made to generate signals.
    - Worst case could be, each attempt yields a unique signal. In this case the signal strength is dampened.
    - Best case, each attempt yields a single signal. In this case the signal strength is boosted.

    Args:
        signals (List[Signal]): A signal is a tuple of name and strength.
        trials (int): Total attempts made to generate signals.

    Returns:
        List[Signal]: A list of strength adjusted signals. May not be as long as the input.
    """
    signal_groups = py_.group_by(signals, lambda signal: signal[0])
    signals_ = [
        (
            signal_name,
            (
                # Averaging signal strength values.
                np.mean([signal[const.SIGNAL.STRENGTH] for signal in signals])
                * (len(signals) / trials)  # normalizing coefficient.
            ),
        )
        for signal_name, signals in signal_groups.items()
    ]
    return sorted(
        signals_, key=lambda signal: signal[const.SIGNAL.STRENGTH], reverse=True
    )


@attr.s
class VotePlugin(Plugin):
    """
    An instance of VoteIntentPlugin helps in voting for a strong
    evidence over other candidates.

    **threshold**: Signal strength should atleast match this value, or else it will be dropped.

    This plugin takes into consideration a list of predictions (signals)
    some of which can be strong, (decided by their confidence score for now)
    and weak signals are filtered out. If there is a healthy vote proportion,
    we will consider the winning signal as the true output.

    This class handles signals which are produced by an intent classifier that
    classifies a set of ASR alternatives (strings).

    The voting algorithm here is naive as it is based on heuristics
    and plain counting. This can be improved by using learned trees/forests.

    Ideal design should provide the signals, their strengths (confidence) and
    signal boosters, any contextual information that implies a weak signal has
    more weight than its counterparts.
    """

    threshold: float = attr.ib(default=0.6)
    fallback_intent: str = attr.ib(default=const.S_INTENT_OOS)
    debug: bool = attr.ib(default=False)

    def vote_signal(self, intents: List[Intent], trials: int) -> Intent:
        """
        Reduce a list of intents.

        This is a naive voting algorithm. We filter intents with high confidence.
        Count the frequency of the remaining intents. If the proportion of votes
        goes beyond the expected constituency, then the intent is elected else
        a fallback intent is emitted.

        Args:
            intents (List[Intent]): A list of predictions over ASR output. (size ~ 1-10)
            constituency (float, optional): Threshold for proportion of votes,
                proportion over this qualifies an intent for victory. Defaults to 0.5.

        Returns:
            Intent: Voted signal or fallback in case of no consensus.
        """
        fallback = Intent(name=self.fallback_intent, score=1)
        if not intents:
            return fallback

        intent_signals = [(intent.name, intent.score) for intent in intents]
        intent_signals = adjust_signal_strength(intent_signals, trials)
        main_intent: Signal = intent_signals[0]

        if self.debug:
            change_log_level("DEBUG")
            log.debug("Intents with adjusted signal strength: ")
            log.debug(intent_signals)
            change_log_level("INFO")

        if main_intent[const.SIGNAL.STRENGTH] >= self.threshold:  # type: ignore
            return Intent(
                name=main_intent[const.SIGNAL.NAME],  # type: ignore
                score=main_intent[const.SIGNAL.STRENGTH],  # type: ignore
            )
        return Intent(name=self.fallback_intent, score=1)

    def plugin(self, workflow: Workflow) -> None:
        """
        Plugin to ease workflow io.
        """
        access = self.access
        mutate = self.mutate

        if access and mutate:
            intents, trials = access(workflow)
            intent = self.vote_signal(intents, trials)
            mutate(workflow, intent)
        else:
            raise TypeError(
                "Expected `access` and `mutate` to be Callable,"
                f" got access={type(access)} mutate={type(mutate)}"
            )

    def __call__(self) -> PluginFn:
        """
        Convenience.
        """
        return self.plugin

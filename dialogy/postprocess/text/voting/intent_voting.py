"""
This module provides utilities to handle multiple intents from each
alternative from the ASR.
"""
from typing import Any, List, Optional

import numpy as np
import pydash as py_  # type: ignore

from dialogy import constants as const
from dialogy.plugin import Plugin
from dialogy.types import Signal
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.utils.logger import change_log_level, log
from dialogy.workflow import Workflow


def adjust_signal_strength(
    signals: List[Signal],
    trials: int,
    aggregate_fn: Any = np.mean,
) -> List[Signal]:
    """
    Re-evaluate signal strength.

    Re-evaluation is based on frequency of occurrence and strength of each occurrence,
    normalized by trials.

    Here trials are total attempts made to generate signals.
    - Worst case could be, each attempt yields a unique signal. In this case the signal strength is dampened.
    - Best case, each attempt yields a single signal. In this case the signal strength is boosted.

    Returns:
        List[Signal]: A list of strength adjusted signals. May not be as long as the input.

    :param signals: A signal is a tuple of name and strength.
    :type signals: List[Signal]
    :param trials: Total attempts made to generate signals.
    :type trials: int
    :param aggregate_fn: A function to normalize a list of floating point values, defaults to np.mean
    :type aggregate_fn: Any, optional
    :raises TypeError: :code:`aggregate_fn` if passed should be a :code:`callable`.
    :return: A list of normalized signale.
    :rtype: List[Signal]
    """
    # Group intents by name.
    if not callable(aggregate_fn):
        raise TypeError(
            "Expected aggregate_fn to be a callable that"
            f" operates on a list of floats. Found {type(aggregate_fn)} instead."
        )
    signal_groups = py_.group_by(signals, lambda signal: signal[0])
    signals_ = [
        (
            signal_name,
            float(
                # Averaging (or some other aggregate fn) signal strength values.
                aggregate_fn([signal[const.SIGNAL.STRENGTH] for signal in signals])
            ),
            float(len(signals) / trials),
        )
        for signal_name, signals in signal_groups.items()
    ]
    return sorted(
        signals_, key=lambda signal: signal[const.SIGNAL.STRENGTH], reverse=True
    )


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

    def __init__(
        self,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        threshold: float = 0.6,
        consensus: float = 0.2,
        representation: float = 0.3,
        fallback_intent: str = const.S_INTENT_OOS,
        aggregate_fn: Any = np.mean,
        debug: bool = False,
    ):
        super().__init__(access, mutate)
        self.threshold: float = threshold
        self.consensus: float = consensus
        self.representation: float = representation
        self.fallback_intent: str = fallback_intent
        self.aggregate_fn: Any = aggregate_fn
        self.debug: bool = debug

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

        intent_signals = [(intent.name, intent.score, 1.0) for intent in intents]
        intent_signals = adjust_signal_strength(
            intent_signals, trials, aggregate_fn=self.aggregate_fn
        )
        main_intent: Signal = intent_signals[0]
        conflict_intent: Signal = (
            intent_signals[1] if len(intent_signals) > 1 else ("_", 0, 0)
        )

        if self.debug:
            change_log_level("DEBUG")
            log.debug("Intents with adjusted signal strength: ")
            log.debug(intent_signals)
            change_log_level("INFO")

        if self.representation > main_intent[const.SIGNAL.REPRESENTATION]:  # type: ignore
            return Intent(name=self.fallback_intent, score=1)

        consensus_achieved = (
            main_intent[const.SIGNAL.STRENGTH] - conflict_intent[const.SIGNAL.STRENGTH]  # type: ignore
            > self.consensus
        )

        strong_signal = main_intent[const.SIGNAL.STRENGTH] > self.threshold  # type: ignore
        if consensus_achieved and strong_signal:
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

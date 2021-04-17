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
from dialogy.utils.logger import change_log_level, debug, log
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

    :param signals: A signal is a tuple of name and strength.
    :type signals: List[Signal]
    :param trials: Total attempts made to generate signals.
    :type trials: int
    :param aggregate_fn: A function to normalize a list of floating point values, defaults to np.mean
    :type aggregate_fn: Any, optional
    :param debug: Log if True.
    :type debug: bool
    :raises TypeError: :code:`aggregate_fn` if passed should be a :code:`callable`.
    :return: A list of normalized signal.
    :rtype: List[Signal]
    """
    # Group intents by name.
    if not callable(aggregate_fn):
        raise TypeError(
            "Expected aggregate_fn to be a callable that"
            f" operates on a list of floats. Found {type(aggregate_fn)} instead."
        )
    signal_groups = py_.group_by(signals, lambda signal: signal[const.SIGNAL.NAME])
    log.debug("signal groups:")
    log.debug(signal_groups)

    signals_ = sorted(
        [
            (
                signal_name,
                float(
                    # Averaging (or some other aggregate fn) signal strength values.
                    aggregate_fn([signal[const.SIGNAL.STRENGTH] for signal in signals])
                ),
                float(len(signals) / trials),
            )
            for signal_name, signals in signal_groups.items()
        ],
        key=lambda signal: signal[const.SIGNAL.REPRESENTATION],
        reverse=True,
    )

    log.debug("sorted and ranked signals:")
    log.debug(signals_)
    return signals_


class VotePlugin(Plugin):
    """
    .. _vote_plugin:
    An instance of VoteIntentPlugin helps in voting for a strong
    evidence over other candidates.

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

    .. warning:: Use this with caution, this is not production ready yet.

    .. ipython:: python

        from dialogy.postprocess.text.voting.intent_voting import VotePlugin
        from dialogy.workflow import Workflow
        from dialogy.types import Intent

        # Let's say we had a normalized set of alternatives that look like:
        transcripts = [
            "yes",
            "yet",
            "yep",
            "ye",
            "<UNK>", # ASR's way of being under-confident about the token
            "no" # expected anomalies in SLU.
        ]

        # We have noticed that concatenation of all the transcripts leads to a situation
        # where a model can't pick signals since there is only one, the one built by
        # concatenation of transcripts. So let's mock the intents for this and continue.

        intents = [Intent(name="affirmative", score=0.8), Intent(name="affirmative", score=0.8),
                    Intent(name="affirmative", score=0.8), Intent(name="affirmative", score=0.8),
                    Intent(name="_oos_", score=0.8), Intent(name="negative", score=0.9)]
        # This situation simulates a single very confident prediction, while the overall group representation
        # paints a different picture.

        # We need to define a function to let the plugin modify the workflow state.

        def update_intent(w, intent):
            w.output[0] = intent
        vote_plugin = VotePlugin(access=lambda w: (w.output, len(w.input[0])), mutate=update_intent, debug=True)()
        workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
        workflow.output = intents
        workflow.run(input_=(transcripts,))


    :param access: A function that expects workflow as an argument and returns a Tuple.
        The Tuple contains: :code:`intents`, :code:`trials`. Here,

        1. :code:`intents` is a :code:`List[T]` where :code:`T` is an :ref:`Intent<intent>`.
        2. :code:`trials` is an :code:`int` that tells us the number of observations that produced the :code:`intents`.

    :type access: Optional[PluginFn]

    :param mutate: A function that places the safest value from the list of :code:`intents` or :code:`fallback_intent`
        in case nothing in the list is safe.
    :type mutate: Optional[PluginFn]

    :param threshold: A threshold for confidence scores for each :ref:`Intent<intent>`.
    :type threshold: float

    :param consensus: We rank each :ref:`Intent<intent>` by confidence score, if the top two have similar and high
        confidence scores, then it is a case of no-consensus. If the top two intents have considerable gap then there
        is consensus. The *considerable gap* is defined by :code:`consensus`.
    :type consensus: float

    :param representation: A percentage that depicts how many votes did an :ref:`Intent<intent>` receive. It is unsafe
        if the confidence threshold is met but representation is poor.
    :type representation: float

    :param fallback_intent: In case we fail to find a strong candidate, we resort to a :code:`fallback_intent`.
    :type fallback_intent: str

    :param aggregate_fn: A function that allows us to aggregate over confidence scores of each :ref:`Intent<intent>`.
    :type aggregate_fn: Any

    :param debug: log intermediates if True.
    :type debug: bool

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
        """
        constructor
        """
        super().__init__(access=access, mutate=mutate, debug=debug)
        self.threshold: float = threshold
        self.consensus: float = consensus
        self.representation: float = representation
        self.fallback_intent: str = fallback_intent
        self.aggregate_fn: Any = aggregate_fn

    @debug(log)
    def vote_signal(self, intents: List[Intent], trials: int) -> Intent:
        """
        Reduce a list of intents.

        This is a naive voting algorithm. We filter intents with high confidence.
        Count the frequency of the remaining intents. If the proportion of votes
        goes beyond the expected constituency, then the intent is elected else
        a fallback intent is emitted.

        :param intents: A list of predictions over ASR output. (size ~ 1-10)
        :type intents: List[Intent]
        :param trials: Number of observations over which the set of intents is obtained.
        :type trials: int
        :return: Voted signal or fallback in case of no consensus.
        :rtype: Intent
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

        log.debug("Intents with adjusted signal strength: ")
        log.debug(intent_signals)

        representative_signal = self.representation <= (main_intent[const.SIGNAL.REPRESENTATION] - conflict_intent[const.SIGNAL.REPRESENTATION])  # type: ignore
        log.debug("representative signal: %s", representative_signal)

        consensus_achieved = (
            main_intent[const.SIGNAL.STRENGTH] - conflict_intent[const.SIGNAL.STRENGTH]  # type: ignore
            > self.consensus
        )
        log.debug(
            "consensus achieved: %s | (%s - %s) > %s",
            consensus_achieved,
            main_intent[const.SIGNAL.STRENGTH],
            conflict_intent[const.SIGNAL.STRENGTH],
            self.consensus,
        )

        strong_signal = main_intent[const.SIGNAL.STRENGTH] > self.threshold  # type: ignore
        log.debug("strong signal: %s", strong_signal)

        if (consensus_achieved or representative_signal) and strong_signal:
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

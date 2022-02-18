"""
.. _AbstractPlugin:

Abstract Plugin
===============

A Plugin transforms the data within the workflow. We use plugins for producing :ref:`intents <Intent>`, :ref:`entities <BaseEntity>`,
filling :ref:`slots <Slot>` and even preparing intermediate data for other plugins. This package ships the abstract base class for creating
other plugins. These offer a base for a few already implemented features like :ref:`book-keeping <PluginBookkeeping>` and :ref:`Guards<Guards>`.

Writing Plugins
================

.. attention::

    We will learn plugin creation by exploring some examples. **It is highly advised to read 
    the** :ref:`Input <Input>` and :ref:`Output <Output>` **sections first.**

Keyword Intent
----------------

Say we have to predict an intent *_greeting_* if the first item in the transcripts have :code:`"hello"`.
This is assuming that the transcripts are ranked by their confidence scores in the descending order.

.. ipython ::

    In [1]: from typing import List
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input, Plugin, Output
       ...: from dialogy.types import Intent

    In [2]: class Transcript2IntentPlugin(Plugin):
       ...:     def __init__(self, dest=None, **kwargs):
       ...:         super().__init__(dest=dest, **kwargs)
       ...:         
       ...:     def greet(self, transcripts: List[str]) -> List[Intent]:
       ...:         if not transcripts:
       ...:             return []
       ...:
       ...:         best_transcript, *rest = transcripts
       ...:
       ...:         if "hello" in best_transcript:
       ...:             return [Intent(name="_greeting_", score=1.0)]
       ...:         else:
       ...:             return []
       ...:
       ...:     def utility(self, input_: Input, output: Output) -> List[Intent]:
       ...:         return self.greet(input_.transcripts)

    In [3]: transcript2intent   = Transcript2IntentPlugin(dest="output.intents")
       ...: workflow            = Workflow([transcript2intent])
       ...: input_, output      = workflow.run(Input(utterances=[[{"transcript": "hello"}]]))
       ...: # The last expression provides us a snapshot of the workflow's 
       ...: # input and output after all plugins have been executed.
       ...: # These aren't the Input and Output objects, but their `dict` equivalents.

    In [4]: # we can see the utterance that we set 
       ...: # and the derived field `transcript` that we used within the plugin.
       ...: # Other values are defaults.
       ...: input_

    In [5]: # we can see that the _greeting_ intent has been set.
       ...: output

Heuristic based Intent
------------------------

This problem requires us to predict *_greeting_* if the word :code:`"hello"`
is present at least 6 times across all utterances. To help us with this, 
we will import an existing plugin: :ref:`MergeASROutputPlugin <merge_asr_output_plugin>`.

.. ipython ::
    :okwarning:

    In [6]: from collections import Counter
       ...: from dialogy.plugins import MergeASROutputPlugin

    In [7]: class HeuristicBasedIntentPlugin(Plugin):
       ...:     def __init__(self, threshold=0, dest=None, **kwargs):
       ...:         super().__init__(dest=dest, **kwargs)
       ...:         self.threshold = threshold
       ...: 
       ...:     def greet(self, clf_features: List[str]) -> List[Intent]:
       ...:         if not clf_features:
       ...:             return []
       ...:
       ...:         feature = clf_features[0]
       ...:         word_frequency = Counter(feature.split())
       ...:         if word_frequency.get("hello", 0) >= self.threshold:
       ...:             return [Intent(name="_greeting_", score=1.0)]
       ...:         else:
       ...:             return []
       ...:     def utility(self, input_: Input, output: Output) -> List[Intent]:
       ...:         return self.greet(input_.clf_feature)

    In [8]: heuristic_based_intent  = HeuristicBasedIntentPlugin(threshold=6, dest="output.intents")
       ...: merge_asr_output_plugin = MergeASROutputPlugin(dest="input.clf_feature")
       ...: workflow                = Workflow([merge_asr_output_plugin, heuristic_based_intent])
       ...: input_, output          = workflow.run(
       ...:    Input(utterances=[
       ...:        [{"transcript": "hello is anyone there"},
       ...:         {"transcript": "yellow is anyone here"},
       ...:         {"transcript": "hello is one here"},
       ...:         {"transcript": "hello is one there"},
       ...:         {"transcript": "hello if one here"},
       ...:         {"transcript": "hello in one here"},
       ...:         {"transcript": "hello ip one here"}]
       ...:    ])
       ...: )

    In [9]: # let's check the snapshots again.
       ...: # Pay close attention to `clf_feature`
       ...: # it wasn't set in the previous example.
       ...: # This time, it was set by the `MergeASROutputPlugin` plugin 
       ...: # as it had the dest = "input.clf_feature"
       ...: input_

    In [10]: output


Guarding plugins
----------------

It may seem useful to not run plugins all the time. In this case, if we knew the current state
of the conversation we could decide to not run our naive plugin. Say a state where we are expecting numbers? 
So let's look at an example where we prevent plugins from execution using :code:`guards`.

.. ipython ::
    :okexcept:

    In [1]: heuristic_based_intent  = HeuristicBasedIntentPlugin(
       ...:     threshold=6,
       ...:     dest="output.intents",
       ...:     guards=[lambda i, o: i.current_state == "STATE_EXPECTING_NUMBERS"]
       ...: )
       ...: merge_asr_output_plugin = MergeASROutputPlugin(dest="input.clf_feature")
       ...: workflow                = Workflow([merge_asr_output_plugin, heuristic_based_intent])
       ...: in_                     = Input(utterances=[[
       ...:                                 {"transcript": "hello is anyone there"},
       ...:                                 {"transcript": "yellow is anyone here"},
       ...:                                 {"transcript": "hello is one here"},
       ...:                                 {"transcript": "hello is one there"},
       ...:                                 {"transcript": "hello if one here"},
       ...:                                 {"transcript": "hello in one here"},
       ...:                                 {"transcript": "hello ip one here"}]]) 
       ...: input_, output          = workflow.run(in_)

    In [2]: # Oops we forgot to set the current state within the Input!
       ...: output

    In [3]: workflow            = Workflow([merge_asr_output_plugin, heuristic_based_intent])
       ...: in_.current_state   = "STATE_EXPECTING_NUMBERS"
       ...: # We get a FrozenInstanceError because Input and Output instances are immutable.

    In [4]: # We can use the following to create a new instance of Input instead.
       ...: in_ = Input.from_dict({"current_state": "STATE_EXPECTING_NUMBERS"}, reference=in_)
       ...: input_, output  = workflow.run(in_)

    In [4]: # In this case, we don't see anything set as the 
       ...: # HeuristicBasedIntentPlugin was prevented
       ...: # by its guarding conditions.
       ...: output

    In [5]: # However, `clf_features` are set since we never wrote guards for 
       ...: # the MergeASROutputPlugin.
       ...: input_

Update Plans
------------

You may need to write plugins that generate an :ref:`Intent <Intent>` or :ref:`BaseEntity <BaseEntity>`, there
is also a category of plugins that might be required for modifications. Like the :ref:`RuleBasedSlotFillerPlugin <RuleBasedSlotFillerPlugin>`
or the :ref:`CombineDateTimeOverSlots <CombineDateTimeOverSlots>`.

The former updates the :ref:`intents<Intent>` and the latter updates :ref:`time-entities <TimeEntity>`. In these cases, the plugins
also take into account other values. 

Such as, :ref:`CombineDateTimeOverSlots <CombineDateTimeOverSlots>`: 

#. Separates time entities from other entity types.
#. Combines them over slot presence.
#. Rebuilds a full entity list.

This means

#. Some plugins need to replace the entire set of intents or entities.
#. While others need to append their results along with the history of the workflow.

If your plugin belongs to [1], then you need to set :code:`replace_output=True` in the constructor of your plugin.

.. note:: 

    Refer to :ref:`CombineDateTimeOverSlots <CombineDateTimeOverSlots>`.
    It's :ref:`combine_time_entities_from_slots <combinetimeentitiesfromslots>` method shows where we may need to use
    :code:`replace_output=True`.

"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, List, Optional

import dialogy.constants as const
from dialogy.base.input import Input
from dialogy.base.output import Output
from dialogy.utils.logger import logger

if TYPE_CHECKING:  # pragma: no cover
    from dialogy.workflow import Workflow


Guard = Callable[[Input, Output], bool]


class Plugin(ABC):
    """
    Abstract class to be implemented by all plugins.

    :param input_column: Transforms data in this column for a given dataframe, defaults to const.ALTERNATIVES
    :type input_column: str
    :param output_column: Saves transformation in this column for a given dataframe, defaults to None
    :type output_column: Optional[str]
    :param use_transform: Should the transformation be applied while training?, defaults to False
    :type use_transform: bool
    :param dest: The path where plugin output should be saved., defaults to None
    :type dest: Optional[str]
    :param guards: A list of functions that evaluate to bool, defaults to None
    :type guards: Optional[List[Guard]]
    :param debug: Should we print debug logs?, defaults to False
    :type debug: bool, optional
    """

    def __init__(
        self,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        replace_output: bool = False,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
    ) -> None:
        self.debug = debug
        self.guards = guards
        self.dest = dest
        self.replace_output = replace_output
        self.input_column = input_column
        self.output_column = output_column or input_column
        self.use_transform = use_transform

    @abstractmethod
    def utility(self, input_: Input, output: Output) -> Any:
        """
        An abstract method that describes the plugin's functionality.

        :param input: The workflow's input.
        :type input: Input
        :param output: The workflow's output.
        :type output: Output
        :return: The value returned by the plugin.
        :rtype: Any
        """

    def __call__(self, workflow: Workflow) -> None:
        """
        Set workflow with output.

        This important book-keeping method is called by the workflow.

        - If the plugin guards evaluate to :code:`True`, we don't run the plugin's business logic.
        - Otherwise, we obtain the plugins transformation and set it on :code:`self.dest` path within the workflow.
            - This path is a string describing :code:`'input'` or :code:`'output'` and their respective attributes separated by a '.'
            - like: :code:`"input.transcripts"` or :code:`"output.intents"`.
        - The workflow takes care of keeping its :ref:`input<Input>` and :ref:`output<Output>` immutable.

        .. _PluginBookkeeping:

        :param workflow: An instance of :ref:`Workflow <WorkflowClass>`.
        :type workflow: Workflow
        """
        logger.enable(str(self)) if self.debug else logger.disable(str(self))

        if workflow.input is None:
            return

        if workflow.output is None:
            return

        if self.prevent(workflow.input, workflow.output):
            return

        value = self.utility(workflow.input, workflow.output)
        if value is not None and isinstance(self.dest, str):
            workflow.set(self.dest, value, self.replace_output)

    def prevent(self, input_: Input, output: Output) -> bool:
        """
        Decide if the plugin should execute.

        If this method returns true, the plugin's utility method will not be called.

        .. _Guards:

        :return: prevent plugin execution if True.
        :rtype: bool
        """
        if not self.guards:
            return False
        return any(guard(input_, output) for guard in self.guards)

    def train(self, _: Any) -> Any:
        """
        Train a plugin.
        """
        return None

    def transform(self, training_data: Any) -> Any:
        """
        Transform data for a plugin in the workflow.
        """
        if not self.use_transform:
            return training_data
        return training_data

    def __str__(self) -> str:
        return self.__class__.__name__

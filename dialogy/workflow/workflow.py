"""
The :ref:`Workflow<WorkflowClass>` represents a black box for an SLU microservice, and its terminals, :ref:`input <Input>` and :ref:`output <Output>`
represent request response structure of the SLU API.

.. note::

    The :ref:`Input<Input>` has some extra properties that aren't part of the SLU API.
    We have kept reserves for intermediates, and flattened as most other nested inputs 
    aren't required and add to bloat.

.. attention::

    :ref:`Input<Input>` and :ref:`Output<Output>` instances are immutable.

What does it do?
----------------

Produce the response for a single turn of a conversation. It recieves (not an exhaustive list):

- Utterance.
- Timezone
- Language code
- Locale
- Current State of the conversation
- Slot tracker


as :ref:`inputs<Input>`, parses these, produces a few intermediates and finally returns the :ref:`intent <Intent>` 
and optionally :ref:`entities <BaseEntity>`. Details will be documented within the specific plugins.

.. mermaid::

    classDiagram
        direction TB
        Workflow --> "1" Input: has
        Workflow --> "1" Output: has
        Workflow --> "many" Plugin: has

        class Workflow {
            Workflow: +Input input
            Workflow: +Output output
            Workflow: +set(path: str, value: Any)
            Workflow: +run(input: Input)
        }

        class Input {
            +List~Utterance~ utterance
            +int reference_time
            +str current_state
            +str lang
            +str locale
            +dict slot_tracker
            +str timezone
            +dict json()
        }

        class Output {
            +List~Intent~ intents
            +List~BaseEntity~ entities
            +dict json()
        }

        <<abstract>> Plugin
        class Plugin {
            +str dest
            *any utility(input: Input, output: Output)
        }



How does it do it?
------------------

- A workflow contains a sequence of :ref:`plugins <AbstractPlugin>`. The sequence is important.
- The sequence describes the order in which :ref:`plugins <AbstractPlugin>` are run.
- The plugins can save their output within the workflow's :ref:`input<Input>` or :ref:`output<Output>`.
- After execution of all plugins, the :ref:`workflow <WorkflowClass>` returns a pair of serialized :ref:`input<Input>` and :ref:`output<Output>`.


.. mermaid::

    flowchart TB

        subgraph Workflow

            subgraph input
                utterance
                reference_time
            end

            subgraph output
                intents
                entities
            end

            input --> plugin
            output --> plugin
            plugin -->|update| input
            plugin -->|update| output
            plugin -->|foreach| plugin

        end
        output --> output_json
        input --> input_json

        output_json --> workflow_output
        input_json --> workflow_output

        subgraph Response
            output_json
        end

"""
from __future__ import annotations

import time

import typing
from typing import List

import attr
import pandas as pd

from threading import Lock
from pprint import pformat
import asyncio, nest_asyncio
from collections import OrderedDict

from dialogy import constants as const
from dialogy.base.input import Input
from dialogy.base.output import Output
from dialogy.base.plugin import Plugin
from dialogy.utils.logger import logger


@attr.s
class Workflow:
    """
    SLU API blackbox.

    .. _WorkflowClass:
    """

    plugins = attr.ib(
        factory=list,
        type=List[Plugin],
        validator=attr.validators.instance_of(list),
    )
    """
    List of :ref:`plugins <AbstractPlugin>`.
    """

    debug = attr.ib(
        type=bool, default=False, validator=attr.validators.instance_of(bool)
    )
    """
    Switch on/off the debug logs for the workflow.
    """

    lock: Lock
    """
    A :ref:`plugin <PluginClass>` may not be thread-safe. Synchronization lock will
    prevent race conditions.
    """

    NON_SERIALIZABLE_FIELDS = [const.PLUGINS, const.DEBUG, const.LOCK]

    def __attrs_post_init__(self) -> None:
        """
        Post init hook.
        """
        self.lock = Lock()

    @typing.no_type_check
    def log_output(self, executed_plugin: Plugin, input: Input, output: Output) -> None:
        # PluginProxy
        if hasattr(executed_plugin, "plugin_name"):
            plugins_executed_names = executed_plugin.plugin_name
        # PluginProxyFused
        elif hasattr(executed_plugin, "plugins"):
            plugins_executed_names = executed_plugin.plugins
        else:
            plugins_executed_names = str(executed_plugin)

        output = {
            "Resultant Transcripts": input.utterances,
            "Resultant Feature Input to Classifier": input.clf_feature,
            "Resultant Output intent": [] if not output.intents else output.intents[0],
            "Resultant Output entities": output.entities
        }
        logger.debug(f"Executed plugin(s) - {plugins_executed_names} \n {pformat(output, sort_dicts=False)}")

    async def run(self, input: Input, output: Output = None, **kwargs):  # type: ignore
        """
        .. _workflow_run:

        Get final results from the workflow.

        The current workflow exhibits the following simple procedure:
        pre-processing -> inference -> post-processing.

        Update input, output attributes.

        We iterate through pre/post processing functions and update the input and
        output attributes of the class. It is expected that pre-processing functions
        would modify the input, and post-processing functions would modify the output.
        """
        history = {}
        if not output:
            output = Output()

        for plugin in self.plugins:
            if not callable(plugin):
                raise TypeError(f"{plugin=} is not a callable")

            # logs are available only when debug=False during class initialization
            if self.debug:
                history = {
                    "plugin": plugin,
                    "before": {
                        "input": input.dict(),
                        "output": output.dict(),
                    },
                }

            start = time.perf_counter()
            # with self.lock:
            # Removing the lock as plugins are
            # expected to be implemented in a thread safe manner
            input, output = await plugin(input, output, **kwargs)
            end = time.perf_counter()
            try:
                self.log_output(plugin, input, output)
            except Exception as e:
                logger.debug(f"logging resultant output after "
                             f"plugin execution failed because of {e}")
            # logs are available only when debug=False during class initialization
            if self.debug:
                history["after"] = {
                    "input": input.dict(),
                    "output": output.dict(),
                }
                history["perf"] = round(end - start, 4)

        return input, output

    def train(self, training_data: pd.DataFrame) -> Workflow:
        """
        Train all the plugins in the workflow.

        Plugin's have a no-op train method by default. The one's that do require training
        should override this method. All trainable plugins manage their data validation
        (in case the data isn't suitable for them) and saving/loading artifacts.

        :param training_data: [description]
        :type training_data: pd.DataFrame
        """
        for plugin in self.plugins:
            plugin.train(training_data)
            loop = asyncio.get_event_loop()
            nest_asyncio.apply(loop)
            coroutine = plugin.transform(training_data)
            transformed_data = loop.run_until_complete(coroutine)
            if transformed_data is not None:
                training_data = transformed_data
        return self

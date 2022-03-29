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

import copy
import time
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

import attr
import pandas as pd

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

    input: Optional[Input] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(Input)),
    )
    """
    Represents the SLU API request object. A few nested properties and intermediates are flattened out
    for readability.
    """

    output: Optional[Output] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(Output)),
    )
    """
    Represents the SLU API response object.
    """

    debug = attr.ib(
        type=bool, default=False, validator=attr.validators.instance_of(bool)
    )
    """
    Switch on/off the debug logs for the workflow.
    """
    lock: Lock
    """
    A :ref:`workflow <WorkflowClass>` isn't thread-safe by itself. We need locks
    to prevent race conditions.
    """
    NON_SERIALIZABLE_FIELDS = [const.PLUGINS, const.DEBUG, const.LOCK]

    def __attrs_post_init__(self) -> None:
        """
        Post init hook.
        """
        self.__reset()
        self.lock = Lock()
        for plugin in self.plugins:
            if isinstance(plugin, Plugin):
                plugin.debug = self.debug & plugin.debug

    def __reset(self) -> None:
        """
        Use this method to keep workflow-io in the same format as expected.
        """
        self.input = None
        self.output = Output()

    def set(self, path: str, value: Any, replace: bool = False) -> Workflow:
        """
        Set attribute path with value.

        This method (re)-sets the input or output object without losing information
        from previous instances.

        :param path: A '.' separated attribute path.
        :type path: str
        :param value: A value to set.
        :type value: Any
        :return: This instance
        :rtype: Workflow
        """
        dest, attribute = path.split(".")

        if dest == const.INPUT:
            self.input = Input.from_dict({attribute: value}, reference=self.input)
        elif attribute in const.OUTPUT_ATTRIBUTES and isinstance(value, (list, dict)):
            if not replace and isinstance(value, list):
                previous_value = self.output.intents if attribute == const.INTENTS else self.output.entities  # type: ignore

                value = sorted(
                    previous_value + value,
                    key=lambda parse: parse.score or 0,
                    reverse=True,
                )

            self.output = Output.from_dict({attribute: value}, reference=self.output)

        elif dest == const.OUTPUT:
            raise ValueError(f"{value=} should be a List[Intent] or List[BaseEntity].")
        else:
            raise ValueError(f"{path} is not a valid path.")
        return self

    def execute(self) -> Workflow:
        """
        Update input, output attributes.

        We iterate through pre/post processing functions and update the input and
        output attributes of the class. It is expected that pre-processing functions
        would modify the input, and post-processing functions would modify the output.
        """
        history = {}
        for plugin in self.plugins:
            if not callable(plugin):
                raise TypeError(f"{plugin=} is not a callable")

            # logs are available only when debug=False during class initialization
            if self.debug:
                history = {
                    "plugin": plugin,
                    "before": {
                        "input": self.input,
                        "output": self.output,
                    },
                }
            start = time.perf_counter()
            plugin(self)
            end = time.perf_counter()
            # logs are available only when debug=False during class initialization
            if self.debug:
                history["after"] = {
                    "input": self.input,
                    "output": self.output,
                }
                history["perf"] = round(end - start, 4)
            if history:
                logger.debug(history)
        return self

    def run(self, input_: Input) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        .. _workflow_run:

        Get final results from the workflow.

        The current workflow exhibits the following simple procedure:
        pre-processing -> inference -> post-processing.
        """
        with self.lock:
            self.input = input_
            try:
                return self.execute().flush()
            finally:
                self.__reset()

    def flush(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Reset :code:`workflow.input` and :code:`workflow.output`.
        """
        if self.input is None or self.output is None:
            return {}, {}
        input_ = copy.deepcopy(self.input.json())
        output = copy.deepcopy(self.output.json())
        self.__reset()
        return input_, output

    def json(self) -> Dict[str, Any]:
        """
        Represent the workflow as a python dict.

        :rtype: Dict[str, Any]
        """
        return attr.asdict(
            self,
            filter=lambda attribute, _: attribute.name
            not in self.NON_SERIALIZABLE_FIELDS,
        )

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
            transformed_data = plugin.transform(training_data)
            if transformed_data is not None:
                training_data = transformed_data
        return self


47

"""
.. _workflow:

A :code:`workflow` is supposed to run tasks that can be anticipated well in advance.

Here are few demo's where you can see mock :code:`workflow` in action.

- :ref:`RuleBasedSlotFillerPlugin<rule_slot_filler>`
- :ref:`VotePlugin<vote_plugin>`
- :ref:`DucklingPlugin<duckling_plugin>`

A workflow is a hollow conduit, think of a vertically hanging pipe without any medium. If you were to drop a block of ...
`anything`? through it, it would pass through with a thud on the ground `(yes we assumed gravity)`.

Structure
----------

A workflow allows flexibility, that's why. There is very little structure to it. We have:

- input
- output
- plugins

Apart from these, we expect at the core, an inference function with machine learning models. Which ones? A N Y ones.
As long as you have the compute, there is no restriction. Use statistical models or DL or a bunch of conditions,
your :ref:`Workflow <Workflow>` won't judge you.

Advantages
-----------

The :ref:`Plugin<plugin>` concept takes care of the sauciness 🍅 of this project. Any functionality can be bundled into
a :ref:`Plugin<plugin>` and they are portable over to foreign workflows. A :ref:`Plugin<plugin>` proxies inputs through
an :code:`access` function (an argument to every :ref:`Plugin<plugin>`) and relays output through a :code:`mutate`
function (another argument for every :ref:`Plugin<plugin>`). These two functions define interactions between many many
(sic) :ref:`Plugins<plugin>` without knowing the inner workings of a :ref:`Workflow <workflow>`.

Take a look at :ref:`DucklingPlugin <duckling_plugin>`, this plugin handles inputs, manages the default :code:`json` output
into neatly bundled :ref:`BaseEntity <base_entity>` and other similar classes. Another plugin
:ref:`RuleBasedSlotFillerPlugin<rule_slot_filler>` takes care of slot names and the entity types that should be filled
within.

If your classifier predicts an :ref:`Intent<intent>` with :ref:`Slots<slot>` supporting any of those entities, then
slot-filling is not a worry.

The aim of this project is to be largest supplier of plugins for SLU applications.

.. warning:: The :ref:`Workflow<workflow>` class is not supposed to be used as it is. Ideally it should have been an
    abstract class. There are some design considerations which make that a bad choice. We want methods to be overridden
    to offer flexibility of use.
"""
import json
import time
from typing import Any, Dict, List, Union

import attr
import pandas as pd  # type: ignore
from tqdm import tqdm  # type: ignore

from dialogy import constants as const
from dialogy.base.plugin import Plugin
from dialogy.utils.logger import logger


@attr.s
class Workflow:
    """
    This is a light but fairly flexible workflow for building a machine learning pipeline.

    Requirements
    - A list of pre-processing functions.
    - A list of post-processing functions.

    Abstract classes put constraints on method signatures which isn't desired because a couple of methods
    here could use more arguments, say, `load_model()` requires `path` and `version` and in some other cases
    `path`, `version` and `language`.

    :param plugins: A list of functions to execute before inference.
    :type plugins: Optional[List[PluginFn]]
    :param debug: log level shifts to debug if True.
    :type debug: bool
    """

    plugins = attr.ib(
        factory=list,
        type=List[Plugin],
        validator=attr.validators.instance_of(list),
    )
    input: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    output: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    debug = attr.ib(
        type=bool, default=False, validator=attr.validators.instance_of(bool)
    )
    NON_SERIALIZABLE_FIELDS = [const.PLUGINS, const.DEBUG]

    def __attrs_post_init__(self) -> None:
        """
        Post init hook.
        """
        self.set_io()

    def set_io(self) -> None:
        """
        Use this method to keep workflow-io in the same format as expected.
        """
        self.input: Dict[str, Any] = {}
        self.output: Dict[str, Any] = {const.INTENTS: [], const.ENTITIES: []}

    def execute(self) -> None:
        """
        Update input, output attributes.

        We iterate through pre/post processing functions and update the input and
        output attributes of the class. It is expected that pre-processing functions
        would modify the input, and post-processing functions would modify the output.

        Args:
            processors (`List`): The list of preprocess or postprocess functions.

        Raises:
            `TypeError`: If any element in processors list is not a Callable.
        """
        history = {}
        for plugin in self.plugins:
            if not callable(plugin):
                raise TypeError(f"{plugin=} is not a callable")

            # logs are available only when debug=True during class initialization
            if self.debug:
                history = {
                    "plugin": plugin,
                    "before": {
                        "input": self.input,
                        "output": self.output,
                    },
                }
            start = time.perf_counter()
            plugin()(self)
            end = time.perf_counter()
            # logs are available only when debug=True during class initialization
            if self.debug:
                history["after"] = {
                    "input": self.input,
                    "output": self.output,
                }
                history["perf"] = round(end - start, 4)
            if history:
                logger.debug(history)

    def run(self, input_: Any) -> Any:
        """
        .. _workflow_run:

        Get final results from the workflow.

        The current workflow exhibits the following simple procedure:
        pre-processing -> inference -> post-processing.

        Args:
            input_ (`Any`): This function receives any arbitrary input. Subclasses may enforce
            a stronger check.

        Returns:
            (`Any`): This function can return any arbitrary value. Subclasses may enforce a stronger check.
        """
        self.input = input_
        self.execute()
        return self.output

    def flush(self) -> None:
        """
        Reset :code:`workflow.input` and :code:`workflow.output`.
        """
        self.set_io()

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

    def train(self, training_data: pd.DataFrame) -> None:
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

    def prediction_labels(
        self, testing_data: pd.DataFrame, id_: Union[str, int]
    ) -> pd.DataFrame:
        """
        Evaluate the workflow with all the embedded plugins.

        Plugins can be evaluated individually for fine-tuning but since there are interactions
        between them, we need to evaluate them all together. This helps in cases where these interactions
        are a cause of a model's poor performance.

        This method doesn't mutate the given test dataset, instead we produce results with the same `id_`
        so that they can be joined and studied together.

        :param testing_data: A pandas DataFrame containing the testing data.
        :type testing_data: pd.DataFrame
        :param id_: The join parameter, which is used to join the testing data with the ground truth data.
        :type id_: Union[str, int]
        :return: A pandas DataFrame containing the workflow output.
        :rtype: pd.DataFrame
        """
        results = []
        for _, row in tqdm(testing_data.iterrows(), total=len(testing_data)):
            self.run(
                input_={
                    const.CLASSIFICATION_INPUT: json.loads(row[const.DATA])[
                        const.ALTERNATIVES
                    ]
                }
            )
            intents = self.output.get(const.INTENTS, [])
            if intents:
                results.append(
                    {
                        id_: row[id_],
                        const.INTENT: intents[0].name,
                        const.SCORE: intents[0].score,
                    }
                )
        return pd.DataFrame(results)

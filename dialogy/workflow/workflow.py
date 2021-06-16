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
- preprocessors
- postprocessors

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
from pprint import pformat
from typing import Any, Callable, Dict, List

import attr

from dialogy import constants as const
from dialogy.utils.logger import dbg, log

PluginFn = Callable[["Workflow"], None]


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

    :param preprocessors: A list of functions to execute before inference.
    :type preprocessors: Optional[List[PluginFn]]
    :param postprocessors: A list of functions to execute after inference.
    :type postprocessors: Optional[List[PluginFn]]
    :param debug: log level shifts to debug if True.
    :type debug: bool
    """

    input: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    output: Dict[str, Any] = attr.ib(factory=dict, kw_only=True)
    debug = attr.ib(
        type=bool, default=False, validator=attr.validators.instance_of(bool)
    )
    preprocessors = attr.ib(
        factory=list,
        type=List[PluginFn],
        validator=attr.validators.instance_of(list),
        kw_only=True,
    )
    postprocessors = attr.ib(
        factory=list,
        type=List[PluginFn],
        validator=attr.validators.instance_of(list),
        kw_only=True,
    )
    NON_SERIALIZABLE_FIELDS = [const.PREPROCESSORS, const.POSTPROCESSORS, const.DEBUG]

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
        self.output: Dict[str, Any] = {}

    def load_model(self) -> None:
        """
        Override method in sub-class to load model(s).

        Raises:
            NotImplementedError: Safeguard against using this class directly.
        """
        class_name = self.__class__.__name__
        raise NotImplementedError(
            f"Override method `load_model` in class {class_name}."
        )

    @dbg(log)
    def update(self, processor_type: str, processors: List[PluginFn]) -> None:
        """
        Update input, output attributes.

        We iterate through pre/post processing functions and update the input and
        output attributes of the class. It is expected that pre-processing functions
        would modify the input, and post-processing functions would modify the output.

        Args:
            processor_type (`str`): One of ["__preprocessor", "__postprocessor"]
            processors (`List`): The list of preprocess or postprocess functions.

        Raises:
            `TypeError`: If any element in processors list is not a Callable.
        """
        for processor in processors:
            if not callable(processor):
                raise TypeError(f"{processor_type}={processor} is not a callable")

            # logs are available only when debug=True during class initialization
            log.debug(
                pformat(
                    {
                        "stage": "Before",
                        "type": processor_type,
                        "plugin": processor,
                        "input": self.input,
                        "output": self.output,
                    }
                )
            )
            processor(self)
            # logs are available only when debug=True during class initialization
            log.debug(
                pformat(
                    {
                        "stage": "After",
                        "type": processor_type,
                        "plugin": processor,
                        "input": self.input,
                        "output": self.output,
                    }
                )
            )

    def preprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses preprocessors over the `update` method, expect input to change.
        """
        self.update(const.PREPROCESSORS, self.preprocessors)

    def postprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses postprocessors over the `update` method, expect output to change.
        """
        self.update(const.POSTPROCESSORS, self.postprocessors)

    def inference(self) -> None:
        """
        Get model predictions.

        Depending on the number of models in use. This place can be used to collate results, sort, filter, etc.

        Raises:
            `NotImplementedError`: This method needs to be implemented by the sub-classes.
        """
        class_name = self.__class__.__name__
        if class_name != "Workflow":
            raise NotImplementedError(
                f"Override method `inference` in class {class_name}."
            )

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
        self.preprocess()
        self.inference()
        self.postprocess()
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

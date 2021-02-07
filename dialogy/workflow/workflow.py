"""
A `workflow` is supposed to run tasks that can be anticipated well in advance. We are prioritizing tasks that can be performed in production
so you may find it odd to miss `train` and `test` methods. This is a deliberate decision since that choice is upto the user and a `workflow`
targets performance in a production environment, where `train` and `test` are not the expected set of tasks, rather `inference` is.

1. Eliminate low-confidence output.
2. Slot-filling.
3. Sorting items by order of confidence.

_What's slot filling?_
> The goal of Slot Filling is to identify from a running dialog, different slots, which correspond to different parameters of the user’s query. For instance, when a user queries for nearby restaurants, key slots for location and preferred food are required for a dialog system to retrieve the appropriate information. Thus, the main challenge in the slot-filling task is to extract the target entity.

[Tutorial](../../tests/workflow/test_workflow.html)

Import Class:
    - Workflow
"""
from pprint import pformat
from typing import List, Callable, Any, Optional
from dialogy import constants
from dialogy.utils.logger import log, change_log_level


PluginFn = Callable[["Workflow"], None]

# = Workflow =
class Workflow:

    """
    This is a light but fairly flexible workflow for building a machine learning pipeline.

    Requirements
    - A list of pre-processing functions.
    - A list of post-processing functions.

    _Why are some methods raising NotImplementedError?_
    > This class is not supposed to be used as it is. Ideally this should have been an abstract class,
    there are some design considerations which make that a bad choice. We want methods to be overridden
    to offer flexibility of use.

    Abstract classes put constraints on method signatures which isn't desired because a couple of methods
    here could use more arguments, say, `load_model()` requires `path` and `version` and in some other cases
    `path`, `version` and `language`.

    All the attributes of the class that are meant for private use, have `__` preceeding their names.
    """

    # == __init__ ==
    def __init__(
        self,
        preprocessors: Optional[List[PluginFn]] = None,
        postprocessors: Optional[List[PluginFn]] = None,
        debug: bool = False,
    ) -> None:
        """
        Setup a Workflow.

        Setup a list of functions to execute before and after `.inference(...)` call.

        Attributes:

        - input (`Any`): The input to a workflow. This is supposed to be flexible.
        - output (`Any`): The outputs of a workflow. This is supposed to be flexible.
        - __preprocessors (`List[PluginFn]`): A list of functions to execute before inference.
        - __postprocessors (`List[PluginFn]`): A list of functions to execute after inference.

        Methods:

        - load_model: Load models
        - update: Update input and output attributes. This is the effect of running either processors.
        - preprocess: Update input attributes. This is the effect of running pre-processors.
        - postprocess: Update output attributes. This is the effect of running post-processors.
        - inference: Model related functionality.
        - run: Wraps over pre/post processing and inference.
        - __log: Log the changes in the input/output as pre/post processing functions execute. REQUIRES log-level set to `DEBUG`.

        Args:

        - preprocessors (`Optional[List[PluginFn]]`): A list of functions to execute before inference. Defaults to None.
        - postprocessors (`Optional[List[PluginFn]]`): A list of functions to execute after inference. Defaults to None.
        - debug (Optional[`bool`]): Changes to input/output are logged if log-level is set to `DEBUG`. Defaults to False.
        """
        # **input**
        #
        # Initially `None`, expects value from the `.run(...)` method.
        self.input: Any = None

        # **output**
        #
        # Initially `None`. Final value depends on the plugins in the workflow.
        self.output: Any = None

        if not isinstance(preprocessors, list):
            # Type check to ensure preprocessors are lists.
            raise TypeError(f"preprocessors={preprocessors} should be a list")
        self.__preprocessors = preprocessors

        if not isinstance(postprocessors, list):
            # Type check to ensure postprocessors are lists.
            raise TypeError(f"preprocessors={postprocessors} should be a list")
        self.__postprocessors = postprocessors

        if debug:
            # We have debug logs, which can be opted in but are off by default.
            change_log_level("DEBUG")
        else:
            # Changing log-level to error would mean, logs from log.debug(...) would not appear.
            change_log_level("ERROR")

    # == load_model ==
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

    # == update ==
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
            if not isinstance(processor, Callable):  # type: ignore
                raise TypeError(f"{processor_type}={processor} is not a callable")

            # logs are available only when debug=True during class initialization
            self.__log("Before", processor_type, processor)
            processor(self)
            # logs are available only when debug=True during class initialization
            self.__log("After", processor_type, processor)

    # == preprocess ==
    def preprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses preprocessors over the `update` method, expect input to change.
        """
        self.update(constants.PREPROCESSORS, self.__preprocessors)

    # == postprocess ==
    def postprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses postprocessors over the `update` method, expect output to change.
        """
        self.update(constants.POSTPROCESSORS, self.__postprocessors)

    # == inference ==
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

    # == run ==
    def run(self, input_: Any) -> Any:
        """
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

    # == __log ==
    def __log(self, message: str, processor_type: str, processor: PluginFn) -> None:
        """
        Log the changes in the input/output as pre/post processing functions execute.

        Args:
            message (`str`): One of ["Before", "After"].
            processor_type (`str`): One of ["__preprocessor", "__postprocessor"].
            processor (`str`): A callable within __preprocessor or __postprocessor.
        """
        log.debug("%s %s %s:", message, processor_type[:-1], processor.__name__)
        log.debug("input")
        log.debug(pformat(self.input))
        log.debug("output")
        log.debug(pformat(self.output))
        log.debug("-" * 30)

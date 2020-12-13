from pprint import pformat
from typing import List, Callable, Any, Optional
from dialogy import constants
from dialogy.utils.logger import log, change_log_level


PluginFn = Callable[['Workflow'], None]


class Workflow:
    def __init__(self, preprocessors: Optional[List[PluginFn]] = None, postprocessors: Optional[List[PluginFn]] = None, debug: bool = False) -> None:
        """
        This is a light but fairly flexible workflow for a machine learning pipeline.

        Requirements
        - A list of pre-processing functions.
        - A list of post-processing functions.

        Why are some methods raising NotImplementedError?      
        This class is not supposed to be used as it is. Ideally this should have been an abstract class,
        there are some design considerations which make that a bad choice. We want methods to be overridden
        to offer flexibility of use.

        Abstract classes put constraints on method signatures which isn't desired because a couple of methods 
        here could use more arguments, say, `load_model()` requires `path` and `version` and in some other cases
        `path`, `version` and `language`.

        All the attributes of the class that are meant for private use, have `__` preceeding their names.

        DO NOT USE THIS CLASS DIRECTLY
        This class is meant for sub-classing, it has few important methods missing, namely inference which does nothing.
        This behaviour is retained for testability of this class.

        Args:
            preprocessors (List[Callable], optional): [description]. Defaults to None.
            postprocessors (List[Callable], optional): [description]. Defaults to None.
            debug (bool, optional): [description]. Defaults to False.
        """
        self.input = None
        self.output = None

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

    def load_model(self) -> None:
        """
        Override method in sub-class to load model(s).

        Raises:
            NotImplementedError: Safeguard against using this class directly.
        """
        class_name = self.__class__.__name__
        raise NotImplementedError(
            f"Override method `load_model` in class {class_name}.")

    def update(self, processor_type: str, processors: List[PluginFn]) -> None:
        """
        Update input, output attributes.

        We iterate through pre/post processing functions and update the input and 
        output attributes of the class. It is expected that pre-processing functions 
        would modify the input, and post-processing functions would modify the output. 

        Args:
            processor_type (str): One of ["__preprocessor", "__postprocessor"]
            processors (List): The list of preprocess or postprocess functions.

        Raises:
            TypeError: If any element in processors list is not a Callable.
        """
        for processor in processors:
            if not isinstance(processor, Callable):  # type: ignore
                raise TypeError(
                    f"{processor_type}={processor} is not a callable")

            # logs are available only when debug=True during class initialization
            self.__log("Before", processor_type, processor)
            processor(self)
            # logs are available only when debug=True during class initialization
            self.__log("After", processor_type, processor)

    def preprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses preprocessors over the `update` method, expect input to change.
        """
        self.update(constants.PREPROCESSORS, self.__preprocessors)

    def postprocess(self) -> None:
        """
        Convenience over `update` method.

        Uses postprocessors over the `update` method, expect output to change.
        """
        self.update(constants.POSTPROCESSORS, self.__postprocessors)

    def inference(self) -> None:
        """
        Get model predictions.

        Depending on the number of models in use. This place can be used to collate results, sort, filter, etc.

        Raises:
            NotImplementedError: This method needs to be implemented by the sub-classes.
        """
        class_name = self.__class__.__name__
        if class_name != "Workflow":
            raise NotImplementedError(
                f"Override method `inference` in class {class_name}.")

    def run(self, input_: Any) -> Any:
        """
        Get final results from the workflow.

        The current workflow exhibits the following simple procedure:
        pre-processing -> inference -> post-processing.

        We run all three functions and return the final result here.

        Args:
            input_ (Any): This function receives any arbitrary input. Subclasses may enforce
            a stronger check.

        Returns:
            (Any): This function can return any arbitrary value. Subclasses may enforce a stronger check.
        """
        self.input = input_
        self.preprocess()
        self.inference()
        self.postprocess()
        return self.output

    def __log(self, message: str, processor_type: str, processor: PluginFn) -> None:
        """
        Log the changes in the input/output as pre/post processing functions execute.

        Args:
            message (str): One of ["Before", "After"].
            processor_type (str): One of ["__preprocessor", "__postprocessor"].
            processor (str): A callable within __preprocessor or __postprocessor.
        """
        log.debug("%s %s %s:", message,
                  processor_type[:-1], processor.__name__)
        log.debug("input")
        log.debug(pformat(self.input))
        log.debug("output")
        log.debug(pformat(self.output))
        log.debug("-" * 30)

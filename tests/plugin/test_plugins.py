"""
This is a tutorial on creating and using Plugins with Workflows.
"""
import re
from typing import Optional, Any

import attr

from dialogy.plugin import Plugin
from dialogy.workflow import Workflow
from dialogy.types.plugin import PluginFn


def access(workflow: Workflow) -> Any:
    """
    This function would be provided by the
    workflow implementer.
    """
    return workflow.input


def mutate(workflow: Workflow, value: Any) -> Any:
    """
    This function would be provided by the
    workflow implementer.
    """
    workflow.output = value


# == tokenizer_plugin ==
def tokenizer_plugin(
    pattern: str = r" ",
    maxsplit: int = 0,
    flags: int = re.I | re.U,
    access: Optional[PluginFn] = None,
    mutate: Optional[PluginFn] = None,
) -> PluginFn:
    """
    Expects a string from the `access(workflow)` and tokenizes the string.
    Example: "an apple" -> ["an", "apple"]

    Args:

    - pattern (str, optional): The string to be tokenized, probably a sentence or document. Defaults to r" ".
    - maxsplit (int, optional): Number of splits for a given pattern, with 0 being an exception, 0 splits for every pattern match. Defaults to 0.
    - flags ([type], optional): Pattern matching would be case-insensitive and applicable on unicode. Defaults to re.I|re.U.

    Raises:

    - TypeError: If there is no input string.
    - ValueError: If the string is empty (0 length).

    Returns:

    - PluginFn: Tokenizer
    """
    # Always compile strings before using them in loops.
    compiled_pattern = re.compile(pattern, flags=flags)

    def plugin(workflow: Workflow) -> Any:
        if access and mutate:
            # assuming consumers would have `workflow.input` as `str`.
            text = access(workflow)
            if not isinstance(text, str):
                raise TypeError(f"Expected str found {type(text)}.")
            if not text:
                raise ValueError("Expected str of non-zero length.")

            # assuming the previously held value is of no relevance.
            mutate(workflow, compiled_pattern.split(text, maxsplit=maxsplit))
        else:
            raise TypeError("access and mutate should be of type PluginFn.")

    return plugin


# == Plugin as a function with workflow ==
def test_tokenizer_plugin() -> None:
    """
    We will test the tokenizer plugin.
    """
    # create an instance of a `Workflow`.
    # we are calling the `arbitrary_plugin` to get the `plugin` de method.
    workflow = Workflow(
        preprocessors=[tokenizer_plugin(access=access, mutate=mutate)],
        postprocessors=[],
    )
    workflow.run("Mary had a little lambda")

    assert workflow.output == ["Mary", "had", "a", "little", "lambda"]


# == ArbitraryPlugin ==
@attr.s
class ArbitraryPlugin(Plugin):
    """
    A Plugin class example.

    We can create Plugins using python classes. If we extend from
    the [`Plugin`](../dialogy/plugin/plugin.html) class, we get the `access` and `mutate`
    attributes.

    The `access` and `mutate` values are set to `None` because there are cases where you may
    only need to perform computation. Say metric plugins, which could be a set of post-processing
    plugins that evaluate the workflow but have nothing to insert into it.

    These utilities would be forced to hack a value around to satisfy the type-checking, this
    can be avoided by expecting either of the functions to be of type `NoneType` or `PluginFn`.
    """

    access: Optional[PluginFn] = attr.ib(default=None)
    mutate: Optional[PluginFn] = attr.ib(default=None)

    # === plugin ===
    def plugin(self, workflow: Workflow) -> None:
        """
        Expects a tuple from `access(workflow)` that contains numbers and words.

        Where

        - numbers: A list of numbers.
        - words: A list of strings.

        This plugin will:

        - Increase each number in `numbers` by 2.
        - Concatenate " world" after each word in `words`.

        The plugin method is the place for implementing
        plugin logic.

        - If values need to be persisted? store them in class attributes.
        - If A set of validation, API calls etc are dependencies to run the implementation?
        create separate methods and call them here.

        Args:

        - workflow (Workflow): The workflow we possibly want to modify.
        """
        if self.access and self.mutate:
            # We are expecting numbers and words from the workflow.
            # The owner of the workflow defines the access and mutate methods, so
            # as a plugin author, you can document the input and output types and
            # expect things to work.
            numbers, words = self.access(workflow)

            # Trivial data manipulation. A serious example would have been canonicalization
            # of sentences to replace tokens with classes they represent for improving
            # performance in a classification task.
            numbers = [number + 2 for number in numbers]
            words = [word + " world" for word in words]
            self.mutate(workflow, (numbers, words))
        else:
            raise TypeError("access and mutate should be of type PluginFn.")

    # === __call__ ===
    def __call__(self) -> PluginFn:
        # this is required only for code-coverage.
        super().__call__()

        # return the plugin method.
        return self.plugin


# == Plugin as a class with workflow ==
def test_arbitrary_plugin() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=access, mutate=mutate)

    # create an instance of a `Workflow`.
    # we are calling the `arbitrary_plugin` to get the `plugin` de method.
    workflow = Workflow(preprocessors=[arbitrary_plugin()], postprocessors=[])

    # This runs all the `preprocessors` and `postprocessors` provided previously.
    # we can expect our `arbitrary_plugin` will also be used.
    workflow.run(([2, 5], ["hello", "hi"]))

    numbers, words = workflow.output  # pylint: disable=unpacking-non-sequence

    # This test would pass only if our plugin works correctly!
    assert numbers == [4, 7]
    assert words == ["hello world", "hi world"]

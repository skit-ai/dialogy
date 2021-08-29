"""
This is a tutorial on creating and using Plugins with Workflows.
"""
import re
from typing import Any, Optional

from dialogy.base.plugin import Plugin
from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow


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


# == ArbitraryPlugin ==
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

    def __init__(
        self,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        debug=False,
    ):
        super().__init__(access=access, mutate=mutate, debug=debug)

    def utility(self, numbers, words) -> Any:
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
        numbers = [number + 2 for number in numbers]
        words = [word + " world" for word in words]
        return numbers, words


# == Plugin as a class with workflow ==
def test_arbitrary_plugin() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=access, mutate=mutate)

    # create an instance of a `Workflow`.
    # we are calling the `arbitrary_plugin` to get the `plugin` de method.
    workflow = Workflow([arbitrary_plugin])

    # This runs all the `preprocessors` and `postprocessors` provided previously.
    # we can expect our `arbitrary_plugin` will also be used.
    workflow.run(([2, 5], ["hello", "hi"]))

    numbers, words = workflow.output  # pylint: disable=unpacking-non-sequence

    # This test would pass only if our plugin works correctly!
    assert numbers == [4, 7]
    assert words == ["hello world", "hi world"]


def test_arbitrary_plugin_with_debug_mode() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=access, mutate=mutate, debug=True)

    # create an instance of a `Workflow`.
    # we are calling the `arbitrary_plugin` to get the `plugin` de method.
    workflow = Workflow([arbitrary_plugin])

    # This runs all the `preprocessors` and `postprocessors` provided previously.
    # we can expect our `arbitrary_plugin` will also be used.
    workflow.run(([2, 5], ["hello", "hi"]))

    numbers, words = workflow.output  # pylint: disable=unpacking-non-sequence

    # This test would pass only if our plugin works correctly!
    assert numbers == [4, 7]
    assert words == ["hello world", "hi world"]


def test_raw_plugin() -> None:
    plugin = Plugin(access=access, mutate=mutate)
    assert plugin.utility() is None


def test_plugin_train() -> None:
    arbitrary_plugin = ArbitraryPlugin(access=access, mutate=mutate, debug=True)
    assert arbitrary_plugin.train([]) is None


def test_plugin_transform() -> None:
    arbitrary_plugin = ArbitraryPlugin(access=access, mutate=mutate, debug=True)
    assert arbitrary_plugin.transform([]) is None

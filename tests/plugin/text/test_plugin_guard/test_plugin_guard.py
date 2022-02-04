"""
This is a tutorial on creating and using Plugins with Workflows.
"""
import re
from typing import Any, Optional

from dialogy.base.plugin import Plugin
from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow
from dialogy.utils.logger import logger

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
        use_transform: bool = False,
        debug=False,
        state_list: Optional[list] = []
    ):
        super().__init__(
            access=access, mutate=mutate, debug=debug, use_transform=use_transform, state_list = state_list
        )

    def utility(self, ctx, numbers, words) -> Any:
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
def test_guard_flag_true() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=lambda w: (
        w.input["context"], w.input["numbers"], w.input["words"]), mutate=mutate, state_list=["COF_LANG", "COF", "INIT"])
    workflow = Workflow([arbitrary_plugin])

    ctx = {
        "current_state": "COF_LANG",
    }
    
    #output = workflow.run(({"context": "ctx"}, [2, 5], ["hello", "hi"]))
    output = workflow.run(input_={"context": ctx, "numbers": [2, 5], "words": ["hello", "hi"]})
    numbers, words = output  # pylint: disable=unpacking-non-sequence

    # This test would pass only if our plugin works correctly!
    assert numbers == [4, 7]
    assert words == ["hello world", "hi world"]

def test_guard_flag_false() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=lambda w: (
        w.input["context"], w.input["numbers"], w.input["words"]), mutate=mutate, state_list=["COF_LANG", "COF", "INIT"])
    workflow = Workflow([arbitrary_plugin])

    ctx = {
        "current_state": "ABC",
    }
    
    #output = workflow.run(({"context": "ctx"}, [2, 5], ["hello", "hi"]))
    output = workflow.run(input_={"context": ctx, "numbers": [2, 5], "words": ["hello", "hi"]})
    # intents, entities = output  # pylint: disable=unpacking-non-sequence
    logger.info(output["intents"])
    # # This test would pass only if our plugin works correctly!
    assert output["intents"] == []
    assert output["entities"] == []

def test_guard_flag_state_list_not_passed() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(access=lambda w: (
        w.input["context"], w.input["numbers"], w.input["words"]), mutate=mutate)
    workflow = Workflow([arbitrary_plugin])

    ctx = {
        "current_state": "ABC",
    }
    
    output = workflow.run(input_={"context": ctx, "numbers": [2, 5], "words": ["hello", "hi"]})
    numbers, words = output  # pylint: disable=unpacking-non-sequence

    assert numbers == [4, 7]
    assert words == ["hello world", "hi world"]


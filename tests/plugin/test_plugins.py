"""
This is a tutorial on creating and using Plugins with Workflows.
"""
import re
from typing import Any, List, Optional

import pytest

from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import Intent
from dialogy.workflow import Workflow


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
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        use_transform: bool = False,
        debug=False,
    ):
        super().__init__(
            dest=dest, guards=guards, debug=debug, use_transform=use_transform
        )

    async def utility(self, _: Input, __: Output) -> Any:
        return [Intent(name="_greeting_", score=0.9)]


# == Plugin as a class with workflow ==
@pytest.mark.asyncio
async def test_arbitrary_plugin() -> None:
    """
    We will test how an arbitrary-class-based plugin works with a workflow.
    """
    # create an instance of `ArbitraryPlugin`.
    arbitrary_plugin = ArbitraryPlugin(dest="output.intents")

    # create an instance of a `Workflow`.
    # we are calling the `arbitrary_plugin` to get the `plugin` de method.
    workflow = Workflow([arbitrary_plugin])
    input_ = Input(utterances=[[{"transcript": "hello"}]])

    # This runs all the `preprocessors` and `postprocessors` provided previously.
    # we can expect our `arbitrary_plugin` will also be used.
    _, output = await workflow.run(input_)
    first_intent, *rest = output.intents

    # This test would pass only if our plugin works correctly!
    assert first_intent.name == "_greeting_"
    assert rest == []


# def test_arbitrary_plugin_with_debug_mode() -> None:
#     """
#     We will test how an arbitrary-class-based plugin works with a workflow.
#     """
#     # create an instance of `ArbitraryPlugin`.
#     arbitrary_plugin = ArbitraryPlugin(dest="output.intents", debug=False)

#     # create an instance of a `Workflow`.
#     # we are calling the `arbitrary_plugin` to get the `plugin` de method.
#     workflow = Workflow([arbitrary_plugin])

#     # This runs all the `preprocessors` and `postprocessors` provided previously.
#     # we can expect our `arbitrary_plugin` will also be used.
#     output = workflow.run(([2, 5], ["hello", "hi"]))

#     numbers, words = output  # pylint: disable=unpacking-non-sequence

#     # This test would pass only if our plugin works correctly!
#     assert numbers == [4, 7]
#     assert words == ["hello world", "hi world"]


def test_plugin_train() -> None:
    arbitrary_plugin = ArbitraryPlugin(dest="output.intents")
    assert arbitrary_plugin.train([]) is None


def test_plugin_transform_not_use_transform() -> None:
    arbitrary_plugin = ArbitraryPlugin(dest="output.intents", use_transform=False)
    assert arbitrary_plugin.transform([]) == []


def test_plugin_transform() -> None:
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents", debug=False, use_transform=True
    )
    assert arbitrary_plugin.transform([{"a": 1}]) == [{"a": 1}]


@pytest.mark.asyncio
async def test_plugin_guards() -> None:
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents",
        guards=[lambda i, _, p: i.current_state == "COF"],
    )
    input = Input(utterances=[[{"transcript": "hello"}]], current_state="COF")
    output = Output()
    assert arbitrary_plugin.prevent(input, output) is True

    returned_input, returned_output = await arbitrary_plugin(input, output)
    # Output should still be empty
    assert returned_output == output
    assert returned_input == input


@pytest.mark.asyncio
async def test_plugin_no_set_on_invalid_input():
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents",
        guards=[lambda i, _, p: i.current_state == "COF"],
    )
    input = None
    output = Output()
    returned_input, returned_output = await arbitrary_plugin(input, output)
    # Output should still be empty
    assert returned_output == output
    assert returned_input == input


@pytest.mark.asyncio
async def test_plugin_no_set_on_invalid_output():
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents",
        guards=[lambda i, _, p: i.current_state == "COF"],
    )
    input = Input(utterances=[[{"transcript": "hello"}]], current_state="COF")
    output = Output()
    returned_input, returned_output = await arbitrary_plugin(input, output)
    # Output should still be empty
    assert returned_output == output
    assert returned_input == input


def test_plugin_set_path():
    plugin = ArbitraryPlugin(dest="output.original_intent")
    input = Input(utterances=[[{"transcript": "hello"}]])
    output = Output()
    input, output = plugin.set(
        path="output.original_intent",
        value={"name": "test", "score": 0.5},
        input=input,
        output=output,
    )
    assert output.original_intent == {"name": "test", "score": 0.5}


def test_plugin_invalid_set_path():
    """
    We can't set invalid values in plugin.
    """
    plugin = ArbitraryPlugin(dest="invalid.path")
    input = Input(utterances=[[{"transcript": "hello"}]])
    output = Output()
    with pytest.raises(ValueError):
        plugin.set(path="invalid.path", value=[], input=input, output=output)


def test_plugin_invalid_set_attribute():
    """
    We can't set invalid values in plugin.
    """
    plugin = ArbitraryPlugin(dest="output.invalid")
    input = Input(utterances=[[{"transcript": "hello"}]])
    output = Output()
    with pytest.raises(ValueError):
        plugin.set(path="output.invalid", value=[], input=input, output=output)


def test_plugin_invalid_set_value():
    """
    We can't set invalid values in plugin.
    """
    plugin = ArbitraryPlugin(dest="output.intents")
    input = Input(utterances=[[{"transcript": "hello"}]])
    output = Output()
    with pytest.raises(ValueError):
        plugin.set(path="output.intents", value=10, input=input, output=output)

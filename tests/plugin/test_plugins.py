"""
This is a tutorial on creating and using Plugins with Workflows.
"""
import re
from typing import Any, Optional, List

from dialogy.base import Plugin, Guard, Input, Output
from dialogy.workflow import Workflow
from dialogy.types import Intent


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

    def utility(self, _: Input, __: Output) -> Any:
        return [Intent(name="_greeting_", score=.9)]


# == Plugin as a class with workflow ==
def test_arbitrary_plugin() -> None:
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
    _, output = workflow.run(input_)
    first_intent, *rest = output["intents"]

    # This test would pass only if our plugin works correctly!
    assert first_intent["name"] == "_greeting_"
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
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents",
        use_transform=False
    )
    assert arbitrary_plugin.transform([]) == []


def test_plugin_transform() -> None:
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents", debug=False, use_transform=True
    )
    assert arbitrary_plugin.transform([{"a": 1}]) == [{"a": 1}]


def test_plugin_guards() -> None:
    arbitrary_plugin = ArbitraryPlugin(
        dest="output.intents",
        guards=[lambda i, _: i.current_state == "COF"],
    )
    workflow = Workflow().set("input.utterances", ["hello"]).set("input.current_state", "COF")
    assert arbitrary_plugin.prevent(workflow.input, workflow.output) is True
    assert arbitrary_plugin(workflow) is None

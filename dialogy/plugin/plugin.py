"""
.. _plugin:

Module provides access to an abstract plugin class.

Summary

We will summarize a few key points for creating plugins:

-   Don't interact with the workflow directly, use functions to access and mutate.
-   The convention for workflow access is `access(workflow)`.
-   The convention for workflow modification is `mutate(workflow, value)`.
-   **Plugin names must end with Plugin for classes and _plugin for functions.** examples: `Sentence2VecPlugin`, `words2num_plugin`.
"""
from typing import Optional

from dialogy.types.plugin import PluginFn


class Plugin:
    """
    A plugin object interacts with a :ref:`workflow<workflow>`. Workflows expect a set of plugins
    to be inserted into different stages: pre and post processing. A plugin can be conveniently written being unaware of the
    structure of a given [`workflow`](../workflow/workflow.html) by expecting `access` and `mutate` functions.
    """

    def __init__(self, access: Optional[PluginFn], mutate: Optional[PluginFn]) -> None:
        # An `access` function is defined to safely extract data from a workflow.
        self.access = access

        # A `mutate` function allows inserting/overwriting data into a workflow.
        self.mutate = mutate

    def __call__(self) -> PluginFn:
        """
        Build a plugin.

        This method returns a function. Since any functionality can be built into a plugin by
        extending the `Plugin` class but they are expected to work uniformly within a `workflow`,
        all plugins must have a standard API. The `__call__` method exists just for this abstraction.

        A plugin can be designed to do anything, while the `workflow` will expect all plugins
        to have a `__call__()` method.
        """
        ...

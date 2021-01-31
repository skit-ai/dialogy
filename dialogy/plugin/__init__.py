"""Module provides access to an abstract plugin class.

Import classes:
    - Plugin
"""
from abc import ABC
from typing import Optional, Callable

import attr
from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow


# = Plugin =
@attr.s
class Plugin:
    """
    [summary]
    """

    access: Optional[PluginFn] = attr.ib(default=None)
    mutate: Optional[PluginFn] = attr.ib(default=None)

    def exec(self) -> PluginFn:
        """Compulsory method, each Plugin must have a definite role invoked by `exec`
        everything else (initialization etc) can happen through other methods.

        These are required if stateful plugins are needed. This method requires `access` and `mutate`
        functions to interact with the workflow. A workflow can be expected in the closure function.

        Args:
            access (Optional[PluginFn], optional): [description]. Defaults to None.
            mutate (Optional[PluginFn], optional): [description]. Defaults to None.
        """
        ...

"""Module provides access to an abstract plugin class.

Import classes:
    - Plugin
"""
from abc import ABC
from typing import Optional, Callable
from dialogy.types.plugins import PluginFn
from dialogy.workflow import Workflow

class Plugin(ABC):
    def exec(
        self, 
        access: Optional[PluginFn] = None, 
        mutate: Optional[PluginFn] = None
    ) -> PluginFn:
        """Compulsory method, each Plugin must have a definite role invoked by `exec`
        everything else (initialization etc) can happen through other methods.

        These are required if stateful plugins are needed. This method requires `access` and `mutate`
        functions to interact with the workflow. A workflow can be expected in the closure function.

        example:

        ```python
        class Plugin(ABC):
            def exec(self, access: Optional[PluginFn] = None, mutate: Optional[PluginFn] = None) -> None:
                def plugin(workflow):
                    pass
        ```

        Args:
            access (Optional[PluginFn], optional): [description]. Defaults to None.
            mutate (Optional[PluginFn], optional): [description]. Defaults to None.
        """

"""
.. _plugin:

Module provides access to an abstract plugin class.

We will summarize a few key points for creating plugins:

-   Don't interact with the workflow directly, use functions to access and mutate.
-   The convention for workflow access is `access(workflow)`.
-   The convention for workflow modification is `mutate(workflow, value)`.
-   Plugin names must end with Plugin for classes and _plugin for functions.

examples:
- Sentence2VecPlugin
- words2num_plugin
- RuleSlotFilerPlugin
- VotePlugin
"""
from typing import Any, Optional

from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow


class Plugin:
    """
    A :ref:`Plugin <plugin>` instance interacts with a :ref:`workflow<workflow>`. A :ref:`workflow<workflow>` expects
    a set of plugins to be inserted into different stages: pre and post processing.
    A plugin can be conveniently written being unaware of the structure of any :ref:`Workflow <workflow>`
    by expecting `access` and `mutate` functions.

    **Dynamic Inputs**

    An :code:`access` method helps a :ref:`Plugin <plugin>` to require dynamic inputs from the :ref:`workflow<workflow>`
    while a :code:`mutate` method offers a :ref:`Plugin <plugin>` to update the processed output and place them as per
    expectations of the :ref:`workflow<workflow>` implementer's design.

    **Static Inputs**

    In case there are static inputs that won't change at runtime, these can be pre-loaded into the
    :ref:`Plugin <plugin>` by extending it.

    An example for this is:

    .. code-block:: python
        :linenos:
        :emphasize-lines: 14, 20

        class CustomPlugin(Plugin):
            def __init__(
                self,
                access: Optional[PluginFn],
                mutate: Optional[PluginFn]
            ) -> None:
                \"""
                The `.load_corpus()` method reads some corpus.
                This is useful since we expect to read this
                just once and use it throughout the runtime.
                \"""
                self.access = access
                self.mutate = mutate
                self.corpus = None
                self.load_corpus()

            def load_corpus(corpus_dir: str, file_path: str) -> None:
                corpus_file = os.path.join(corpus, file_path)
                with open(corpus_file, "r") as handle:
                    self.corpus = handle.read().splitlines()

    We ship a few :ref:`Plugins <plugin>` with Dialogy, namely:

    1. :ref:`DucklingPlugin <duckling_plugin>` (pre-processing)
    2. :ref:`merge_asr_output_plugin <merge_asr_output_plugin>` (pre-processing)
    3. :ref:`RuleBasedSlotFillerPlugin <rule_slot_filler>` (post-processing)
    4. :ref:`VotePlugin <vote_plugin>` (post-processing)
    """

    def __init__(
        self,
        access: Optional[PluginFn],
        mutate: Optional[PluginFn],
        debug: bool = False,
    ) -> None:
        self.access = access
        self.mutate = mutate
        self.debug = debug

    def utility(self, *args: Any) -> Any:
        ...

    def plugin(self, workflow: Workflow) -> None:
        if self.access:
            args = self.access(workflow)
            value = self.utility(*args)
            if value is not None and self.mutate:
                self.mutate(workflow, value)
        else:
            raise TypeError(
                "Expected access to be functions" f" but {type(self.access)} was found."
            )

    def __call__(self) -> PluginFn:
        """
        Build a plugin.

        This method returns a function. Since any functionality can be built into a plugin by
        extending the `Plugin` class but they are expected to work uniformly within a `workflow`,
        all plugins must have a standard API. The `__call__` method exists just for this abstraction.

        A plugin can be designed to do anything, while the `workflow` will expect all plugins
        to have a `__call__()` method.
        """
        return self.plugin

"""
.. _plugin:

Module provides access to a plugin class.

We will summarize a few key points for creating plugins:

-   Don't interact with the workflow directly, use functions to access and mutate.
-   The convention for workflow access is `access(workflow)`.
-   The convention for insertion is `mutate(workflow, value)`.
-   Plugin names must end with Plugin for classes.
"""
from typing import Any, Optional

import dialogy.constants as const
from dialogy.types import PluginFn
from dialogy.utils.logger import logger


class Plugin:
    """
    A :ref:`Plugin <plugin>` object provides utilities that perform a transformation. A :ref:`Plugin <plugin>` object differs
    in behaviour depending on it's purpose. Purpose defines stages in a :ref:`Workflow <workflow>`'s lifecycle.
    These are namely: ``train``, ``test`` and ``production``.

    A :ref:`Plugin <plugin>` object:

    - May be trained, expected during the ``train`` lifecycle.
    - May transform a dataframe, expected during the ``test`` lifecycle.
    - Transforms a datapoint, expected during the ``production`` lifecycle.

    Imagine a workflow processing a dataframe. Sequencing plugins like so:

    .. code-block::

        start -> A -> B -> C -> D -> end

    Let's assume that the plugin B, and C are plugins that can transform data without any training.
    However, plugins A and D require training and transform data. The data transformations differ slightly as per
    the :ref:`workflow<workflow>` life-cycle.

    1. During the training phase:
        1. Plugin A starts training on a dataframe and then transforms the data.
        2. Plugin B, C start transforming the dataframe received from A.
        3. Plugin D starts trains on the dataframe received from C.
    2. During the evaluation phase:
        1. Each plugin performs its own transformation and passes data ahead.

    How does plugin P2 get trained if plugin P1 requires data from an incompatable dataframe?

    .. code-block::

        start -> P1 -> P2 -> end

    Given that the production lifecycle implies that a plugin either receives the base features
    straight from the :ref:`Workflow <workflow>` or its derivates via transformations from pre-existing plugins.

    Therefore we can redefine incompatibility as follows:

    1. Label differences, i.e. P1 trains on Transcription dataframes but P2 trains on Intent Classification dataframes.
    2. Feature differences, i.e. P1 trains on confidence scores but P2 trains on ASR transcripts.

    Plugins require a method for validation to ensure the data they receive matches the data they are expected to process.
    If the validation fails, plugins must not interrupt the training by raising exceptions.

    Speaking from our example, P1 gets trained and P2 remaines untrained. This doesn't sound intuitive but
    that's because we are looking at plugins within a :ref:`workflow<workflow>`. As a remedy, :ref:`plugins<plugins>`
    can be trained in isolation. A plugin author still must provide ``train``, ``transform`` and ``utility``
    methods for a trainable plugin.


    **Input**

    :ref:`Plugin <plugin>` instantiation provides the configuration but transformation is done by applying
    functions on a :ref:`Workflow <workflow>`. This way the seemingly linear sequence of plugins has the freedom to
    access anything committed to the :ref:`Workflow <workflow>`.

    **Output**

    Post transformation we need the plugin to commit a ``value``. This value is not passed to the next plugin, instead we commit
    everything to the :ref:`Workflow <workflow>` by applying a ``mutate`` function with the ``value`` over to the :ref:`Workflow <workflow>`.

    **Trainable Plugins**

    If a :ref:`Plugin <plugin>` is trainable, it must implement these methods:

    1. ``train(x: pd.DataFrame) -> Plugin``
    2. ``utility(...) -> Any``
    3. ``validate(x: pd.DataFrame) -> bool``
    4. ``save() -> Plugin``
    5. ``load() -> Plugin``

    **Transformer Plugins**

    If a :ref:`Plugin <plugin>` transforms data and produces trainable features, it must implement these methods:

    1. ``transform(x: pd.DataFrame) -> pd.DataFrame``
    2. ``utility(...) -> Any``
    3. ``validate(x: pd.DataFrame) -> bool``

    **Base Plugins**

    If a :ref:`Plugin <plugin>` is expected to transform isolated data points (no-training, no feature generation):

    1. ``utility(...) -> Any``
    """

    def __init__(
        self,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        debug: bool = False,
    ) -> None:
        self.access = access
        self.mutate = mutate
        self.debug = debug
        self.use_transform = use_transform
        self.input_column = input_column
        self.output_column = output_column or input_column

    def utility(self, *args: Any) -> Any:
        """
        Transform X -> y.

        This method is called during a :ref:`Workflow <workflow>` run.

        :return: A value that will be passed to the next plugin (if any).
        :rtype: Any
        """
        return None

    def plugin(self, workflow: Any) -> None:
        """
        Abstraction for plugin io.

        :param workflow:
        :type workflow: Workflow
        :raises TypeError: If access method is missing, we can't get inputs for transformation.
        """
        if self.debug:
            logger.enable("dialogy")
        else:
            logger.disable("dialogy")
        if self.access:
            args = self.access(workflow)
            value = self.utility(*args)  # pylint: disable=assignment-from-none
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

    def train(
        self, _: Any
    ) -> Any:  # pylint: disable=unused-argument disable=no-self-use
        """
        Train a plugin.
        """
        return None

    def transform(
        self, training_data: Any
    ) -> Any:  # pylint: disable=unused-argument disable=no-self-use
        """
        Transform data for a plugin in the workflow.
        """
        if not self.use_transform:
            return training_data
        return training_data

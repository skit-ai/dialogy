"""
.. _plugin:

Writing Plugins
################

Plugins are an abstraction over procedures that offer a specific functionality. A plugin abstracts out the way it is fed an input, and the way its output is pushed out.

A discussion about plugins requires a bit of background about worfklows, a :ref:`workflow <workflow>` is an ephemeral datastore. This distinction of roles
between a :ref:`Plugin <plugin>` and a :ref:`Workflow <workflow>` is a **convention** to ensure that :ref:`plugins <plugin>` have some common structure.


Plugin Types
*************

There are three types of plugins:

1. Solitary
2. Transformer
3. Trainable

Solitary
========

A plugin that only interacts during the runtime of a :ref:`workflow <workflow>` is called a *Solitary plugin*.
We can create a Solitary plugin like so:

Methods
-------

The **utility** method describes the feature implemented by the plugin, this is the only required method for Solitary plugins. This method is called
during a workflow's run. If a plugin produces a value, it can also be updated within workflow. Any kind of file reading, config parsing, model loading
should be done during the plugin's initialization. If there are any dynamic inputs required by a plugin, it should be available within the :code:`*args`.

The workflow at runtime needs a common method to invoke to execute plugins. The *nargs* are just to specify a structure,
it is advisable to not house entire logic withing the utility method. Instead just validate inputs and call a separate method for core plugin logic.


**utility** methods must have fast execution times.

    .. ipython::

        In [1]: from typing import Any, Optional, List, Tuple
           ...: from dialogy.base.plugin import Plugin
           ...: from dialogy.types import PluginFn
           ...: from dialogy.workflow import Workflow
           ...:
           ...: class ASolitaryPlugin(Plugin):
           ...:     def __init__(
           ...:         self,
           ...:         access: Optional[PluginFn] = None,
           ...:         mutate: Optional[PluginFn] = None,
           ...:         debug: bool = False
           ...:     ):
           ...:         super().__init__(access=access, mutate=mutate, debug=debug)
           ...:
           ...:     def utility(self, *args: Any) -> Any:
           ...:         return None

Let's take an example of a plugin that concatenates the transcripts from an ASR to a :code:`str`.

    .. ipython::

        In [2]: class MergeASRPlugin(Plugin):
           ...:     def __init__(
           ...:         self,
           ...:         start_token: str = "<s>",
           ...:         end_token: str = "</s>",
           ...:         access: Optional[PluginFn] = None,
           ...:         mutate: Optional[PluginFn] = None,
           ...:         debug: bool = False
           ...:     ):
           ...:         super().__init__(access=access, mutate=mutate, debug=debug)
           ...:         # Always validate the input.
           ...:         self.start_token = start_token
           ...:         self.end_token = end_token
           ...:
           ...:     def concat(self, transcripts: List[str]) -> str:
           ...:         return self.start_token + f"{self.end_token} {self.start_token}".join(transcripts) + self.end_token
           ...:
           ...:     def utility(self, *args: List[str]) -> str:
           ...:         # Always validate the input.
           ...:         return self.concat(args[0])

        In [3]: MergeASRPlugin().utility(["hello world", "hello worlds", "hello word"])

Input
-----

Previously we saw that the utility method produces results on expected inputs. We will now see how to get the same from a workflow.

    .. ipython::

        In [4]: def get_classifier_input(workflow: Workflow) -> Tuple[List[str]]:
           ...:     return (workflow.input["transcripts"],)

This is an accessor function, these expect a workflow instance as their only argument and can return anything currently available.
These accessor functions are written by workflow creators and allow someone to use core plugins as long as plugins specify the input, output types.

Output
-------

Once the plugin produces an output, we may want to store it in the workflow. We rely on mutator functions to send
the plugin output back to the workflow. These are also written by workflow creators.

    .. ipython::

        In [5]: def set_classifier_input(workflow: Workflow, value: str) -> None:
           ...:     '''
           ...:     We would normally overwrite the input but since a workflow
           ...:     loses inputs once run; and returns only a copy of the output,
           ...:     we are creating a new key within the output.
           ...:     '''
           ...:     workflow.output["transcripts"] = value

Integrations
------------

Now we fit the pieces together and can visualize the interactions between a workflow and a plugin.

    .. ipython::

        In [6]: w = Workflow([MergeASRPlugin(access=get_classifier_input, mutate=set_classifier_input)])
           ...: w.output
           ...: w.run({"transcripts": ["hello world", "hello worlds", "hello word"]})
           ...:

Transformer
===========

Transformer plugins are solitary plugins that can additionally transform dataframes. These can be used for producing new features or modify existing ones.

Remember the MergeASRPlugin plugin we have built? it transforms a single data point at runtime. To transform during the training phase of a workflow we need
a **transform** method.

Let's try to build a transformer plugin that will add a new column to a dataframe.

    .. ipython::

        In [7]: import json
           ...: import pandas as pd
           ...:
           ...: class MergeASRPlugin(Plugin):
           ...:     def __init__(
           ...:         self,
           ...:         start_token: str = "<s>",
           ...:         end_token: str = "</s>",
           ...:         access: Optional[PluginFn] = None,
           ...:         mutate: Optional[PluginFn] = None,
           ...:         input_column: str = "alternatives",
           ...:         output_column: Optional[str] = "concat_alternatives",
           ...:         use_transform: bool = True,
           ...:         debug: bool = False
           ...:     ):
           ...:         super().__init__(access=access, mutate=mutate, input_column=input_column, output_column=output_column, use_transform=use_transform, debug=debug)
           ...:         self.start_token = start_token
           ...:         self.end_token = end_token
           ...:
           ...:     def concat(self, transcripts: List[str]) -> str:
           ...:         return self.start_token + f"{self.end_token} {self.start_token}".join(transcripts) + self.end_token
           ...:
           ...:     def utility(self, *args: List[str]) -> str:
           ...:         # Always validate the input.
           ...:         return self.concat(args[0])
           ...:
           ...:     def parse_value(self, value):
           ...:         return self.utility(json.loads(value))
           ...:
           ...:     def transform(self, training_data: pd.DataFrame):
           ...:         if not self.use_transform:
           ...:             return training_data
           ...:
           ...:         training_data[self.output_column] = training_data[self.input_column].apply(self.parse_value)
           ...:         return training_data
           ...:
           ...: df = pd.DataFrame({"alternatives": [json.dumps(["hello world", "helo world"]), json.dumps(["today only", "today"])]})
           ...: MergeASRPlugin(input_column="alternatives", output_column="updated_alternatives").transform(df)

and the lifecycle of this plugin during the training phase will be covered in a later section once we have an understanding of a trainable plugin.

Trainable
=========

Trainable plugins are solitary plugins that can additionally train dataframes. A trainable plugin may optionally be able to transform dataframes as well.
Now we will build a new demo plugin that will train a classifier on a dataframe.

    .. ipython::

        In [8]: import pickle
           ...: from sklearn.tree import DecisionTreeClassifier
           ...: from sklearn.pipeline import Pipeline
           ...: from sklearn.feature_extraction.text import TfidfTransformer
           ...: from sklearn.feature_extraction.text import CountVectorizer
           ...:

        In [9]: class TreeClassifierPlugin(Plugin):
           ...:     def __init__(
           ...:         self,
           ...:         access: Optional[PluginFn] = None,
           ...:         mutate: Optional[PluginFn] = None,
           ...:         random_state: int = 0,
           ...:         x_col: str = "alternatives",
           ...:         y_col: str = "intents",
           ...:         debug: bool = False
           ...:     ):
           ...:         super().__init__(access=access, mutate=mutate, debug=debug)
           ...:         self.model = Pipeline([
           ...:             ('vect', CountVectorizer()),
           ...:             ('tfidf', TfidfTransformer()),
           ...:             ('clf', DecisionTreeClassifier(random_state=random_state))
           ...:         ])
           ...:         self.x_col = x_col
           ...:         self.y_col = y_col
           ...:
           ...:     def train(self, training_data: pd.DataFrame):
           ...:         X = training_data[self.x_col]
           ...:         y = training_data[self.y_col]
           ...:         self.model.fit(X, y)
           ...:
           ...:     def save(self):
           ...:         with open(self.save_path, "wb") as handle:
           ...:             pickle.dump(self.model, handle)
           ...:
           ...:     def load(self):
           ...:         with open(self.save_path, "rb") as handle:
           ...:             self.model = pickle.load(handle)
           ...:
           ...:     def utility(self, *args):
           ...:         return self.model.predict(args)
           ...:
           ...: df = pd.DataFrame({"alternatives": [json.dumps(["yes", "yea"]), json.dumps(["no", "nope"])], "intents": ["affirmative", "negative"]})
           ...:
           ...: def set_classifier_output(workflow, value):
           ...:    workflow.output["intents"] = value
           ...:
           ...: def set_classifier_input(workflow, value):
           ...:    workflow.input["transcripts"] = value

        In [10]: w = Workflow([MergeASRPlugin(access=get_classifier_input, mutate=set_classifier_input, input_column="alternatives", use_transform=True), TreeClassifierPlugin(access=get_classifier_input, mutate=set_classifier_output, x_col="concat_alternatives", y_col="intents")])

        In [11]: w.train(df)

        In [12]: w.run({"transcripts": ["yes"]})

The following code-snippet will help us understand the **train** method of a workflow.

    .. code-block:: python
        :linenos:

        def train(self, training_data: pd.DataFrame)
            for plugin in self.plugins:
                # if a plugin is not trainable, the dataframe is expected to have no side effects.
                plugin.train(training_data)

                # Only if a plugin is a transformer, the dataframe is expected to have side effects.
                transformed_data = plugin.transform(training_data)

                # We update the training dataframe with the transformed data.
                # This behaviour may need changes in the future for handling multi-modal features.
                # Currently this serves the purpose of training plugins with similar data requirements at once.
                if transformed_data is not None:
                    training_data = transformed_data


Notes
*****

- If your plugin needs a model but it need not be trained frequently or uses an off the shelf pre-trained model, then you must build a Solitary plugin.
- A trainable plugin can also have transform methods if it needs to modify a dataframe for other plugins in place.
"""
from abc import ABC, abstractmethod
from typing import Any, Optional

import dialogy.constants as const
from dialogy.types import PluginFn
from dialogy.utils.logger import logger


class Plugin(ABC):
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

    **Solitary Plugins**

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
        self.input_column = input_column
        self.output_column = output_column or input_column
        self.use_transform = use_transform

    @abstractmethod
    def utility(self, *args: Any) -> Any:
        """
        Transform X -> y.

        This method is called during a :ref:`Workflow <workflow>` run.

        :return: A value that will be passed to the next plugin (if any).
        :rtype: Any
        """

    def __call__(self, workflow: Any) -> None:
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

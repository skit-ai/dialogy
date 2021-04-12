"""
A :ref:`Plugin <plugin>` is an abstraction to handle third-party features with custom :ref:`Workflow <workflow>` pipelines.

We offer a :ref:`Workflow <workflow>` that provides a simple API exposed via its :code:`run(input_=X)` method.
The input has no restrictions, the :ref:`Workflow <workflow>` will apply a set of pre-processing functions and
post-processing functions.

The challenge is :ref:`Workflow <workflow>` and :ref:`Plugin <plugin>` are not built usually by the same people.
A tailor-made solution for a :ref:`Workflow <workflow>` hampers the portability of the solution. These can be inserted
in various ways, like methods, or external functions even. The hope here is to encourage better abstraction while
writing plugins. This will help improvement, addition of existing features by keeping them in their separate, isolated,
context-free boxes.

An ideal :ref:`Plugin <plugin>`  must therefore not assume a :ref:`Workflow <workflow>` structure. It must use
abstractions to specify requirements and expect these to be met for safe usage.
"""
from dialogy.plugin.plugin import Plugin, PluginFn

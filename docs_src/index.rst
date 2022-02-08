.. dialogy documentation master file, created by
   sphinx-quickstart on Sun Apr 11 07:39:33 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dialogy
========

.. image:: https://app.travis-ci.com/skit-ai/dialogy.svg?branch=master
    :target: https://app.travis-ci.com/skit-ai/dialogy

.. image:: https://coveralls.io/repos/github/skit-ai/dialogy/badge.svg?branch=master
   :target: https://coveralls.io/github/skit-ai/dialogy?branch=master

.. image:: https://app.codacy.com/project/badge/Grade/03ab1c93c9354def81de73ba04b0d94c
   :target: https://www.codacy.com/gh/skit-ai/dialogy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Vernacular-ai/dialogy&amp;utm_campaign=Badge_Grade

.. image:: https://badge.fury.io/py/dialogy.svg
    :target: https://badge.fury.io/py/dialogy


Dialogy is a library for building and managing SLU applications.

Topics 📄
#########

Listing sections by order of significance. Higher ranking items are helpful in understanding items that are ranked lower.


+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   |                                                                |                                                        Description                                                        |
+===+================================================================+===========================================================================================================================+
| 1 | :ref:`Input <Input>`                                           | A fundamental unit that describes the inputs (along with their derivates) of the inference API.                           |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| 2 | :ref:`Output <Output>`                                         | A fundamental unit that describes the output of the inference API.                                                        |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| 3 | :ref:`Workflow <WorkflowClass>`                                | A workflow *has* an :code:`Input` and an :code:`Output`. It also *contains* :code:`plugins`.                              |
|   |                                                                | The :code:`run(...)` produces the inference API's response.                                                               |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
| 4 | :ref:`Plugin <plugin-abstract>`                                | The base (abstract) class for all plugins.                                                                                |
|   |                                                                |                                                                                                                           |
|   |                                                                | [:ref:`how to write plugins <Writing Plugins>`]                                                                           |
|   |                                                                |                                                                                                                           |
|   |                                                                | This class requires creation of a utility method of the following signature:                                              |
|   |                                                                |                                                                                                                           |
|   |                                                                | .. code:: python                                                                                                          |
|   |                                                                |                                                                                                                           |
|   |                                                                |     def utility(self, input_: Input, output: Output) -> Any:                                                              |
|   |                                                                |        ...                                                                                                                |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   | :ref:`DucklingPlugin<duckling_plugin>`                         | Connects to the Duckling API and returns entities of type:                                                                |
|   |                                                                |                                                                                                                           |
|   |                                                                | #. **date**                                                                                                               |
|   |                                                                | #. **time**                                                                                                               |
|   |                                                                | #. **duration**                                                                                                           |
|   |                                                                | #. **number**                                                                                                             |
|   |                                                                | #. **people**                                                                                                             |
|   |                                                                | #. **plastic-money**                                                                                                      |
|   |                                                                | #. **amount-of-money**                                                                                                    |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   | :ref:`MergeASROutput<merge_asr_output>`                        | Featurizer for the intent classifier model. Concatenates :code:`input.utterances`.                                        |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   | :ref:`XLMRMultiClass<xlmr_classifier>`                         | The intent classifier model as a plugin. Requires :code:`input.clf_feature` and returns `List[Intent]`.                   |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   | :ref:`CombineDateTimeOverSlots <combine_date_time_over_slots>` | This plugin combines date/time entities tracked by the slot filler (previous turns)                                       |
|   |                                                                | with time/date entities extracted in the current turn.                                                                    |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+
|   | :ref:`WERCalibrationPlugin<calibration_plugin>`                | This plugin can only be used with the proprietary ASR of skit.ai. Uses :code:`lm_score` and :score:`am_score` to          |
|   |                                                                | detect if the current set of code:`input.utterances` are too noisy for the intent classifier to use.                      |
+---+----------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------------+


Installation
------------

.. code-block:: bash

   pip install dialogy

Test
----

.. code-block:: bash

   make test

Getting started
---------------

Dialogy's CLI supports building and migration of projects. Migration is hard because a few modules need a forced update but a few others
should be retained by the developer. The lack of this expression makes it hard to migrate smoothly. Building new projects should be fairly simple.

.. code-block:: bash

   dialogy -h
   usage: dialogy [-h] {create,update,train} ...

   positional arguments:
   {create,update,train}
                           Dialogy project utilities.
      create              Create a new project.
      update              Migrate an existing project to the latest template version.
      train               Train a workflow.

   optional arguments:
   -h, --help            show this help message and exit

Project Creation
----------------

.. code-block:: bash

   dialogy create -h
   usage: dialogy create [-h] [--template TEMPLATE] [--dry-run] [--namespace NAMESPACE] [--master] project

   positional arguments:
   project               A directory with this name will be created at the root of command invocation.

   optional arguments:
   -h, --help            show this help message and exit
   --template TEMPLATE
   --dry-run             Make no change to the directory structure.
   --namespace NAMESPACE
                           The github/gitlab user or organization name where the template project lies.
   --master              Download the template's master branch (HEAD) instead of the latest tag.


Contributors
------------

Clone the repository. We use [`poetry <https://python-poetry.org/>`_] to setup dependencies.

.. code-block:: shell

   git clone git@github.com:skit-ai/dialogy.git
   cd dialogy
   # Activate your virtualenv/conda or you may allow poetry take care of it.
   poetry install
   make test

Ensure tests are passing before you start working on your PRs.

[`Read more <https://github.com/skit-ai/dialogy/blob/master/CONTRIBUTING.md>`_]

Further Reading
###############

#. :ref:`Index<genindex>`
#. All Modules

   .. toctree::
      :maxdepth: 1
      :glob:

      ../source/dialogy.base
      ../source/dialogy.plugins.*
      ../source/dialogy.types.*
      ../source/dialogy.workflow
      ../source/dialogy.utils

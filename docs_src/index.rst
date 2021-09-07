.. dialogy documentation master file, created by
   sphinx-quickstart on Sun Apr 11 07:39:33 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Dialogy
========

.. image:: https://travis-ci.com/Vernacular-ai/dialogy.svg?branch=master
    :target: https://travis-ci.com/Vernacular-ai/dialogy

.. image:: https://coveralls.io/repos/github/Vernacular-ai/dialogy/badge.svg?branch=master
   :target: https://coveralls.io/github/Vernacular-ai/dialogy?branch=master

.. image:: https://app.codacy.com/project/badge/Grade/03ab1c93c9354def81de73ba04b0d94c
   :target: https://www.codacy.com/gh/Vernacular-ai/dialogy/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Vernacular-ai/dialogy&amp;utm_campaign=Badge_Grade

.. image:: https://badge.fury.io/py/dialogy.svg
    :target: https://badge.fury.io/py/dialogy

Dialogy is a batteries-included opinionated framework to build machine-learning solutions for speech applications.

-   Plugin-based: Makes it easy to import/export components to other projects.
-   Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy.
-   Progressive: Minimal boilerplate writing to let you focus on your machine learning problems.

Sections 📄
------------
1. :ref:`Index<genindex>`
2. Popular Sections

   1. :ref:`Workflow<workflow>`
   2. :ref:`Plugin<Plugin>`
         1. :ref:`DucklingPlugin<duckling_plugin>`
         2. :ref:`MergeASROutput<merge_asr_output>`
         3. :ref:`WERCalibrationPlugin<calibration_plugin>`
         4. :ref:`RuleBasedSlotFillerPlugin<rule_slot_filler>`
         5. :ref:`VotePlugin<vote_plugin>`
         6. :ref:`XLMRMultiClass<xlmr_classifier>`

3. All Modules

   .. toctree::
      :maxdepth: 1
      :glob:

      ../source/dialogy.*


Installation
------------

.. code-block:: bash

   pip install dialogy

Test
----

.. code-block:: bash

   make test

FAQs
-----

Starting projects
**************************

We have a `template <https://github.com/Vernacular-ai/dialogy-template-simple-transformers>`_
that can help you get started with a SLU project.

.. code-block:: shell

   dialogy create <your_project_name> dialogy-template-simple-transformers

An interactive session will collect a few details and create a project scaffolding ready to use.

.. note:: Popular workflow sub-classes will be accepted after code-review.

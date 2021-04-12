.. dialogy documentation master file, created by
   sphinx-quickstart on Sun Apr 11 07:39:33 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to dialogy's documentation!
===================================

.. toctree::
   :maxdepth: 4
   :caption: Contents:

   ../source/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Dialogy
========

.. image:: https://travis-ci.com/Vernacular-ai/dialogy.svg?branch=master
    :target: https://travis-ci.com/Vernacular-ai/dialogy

.. image:: https://badge.fury.io/py/dialogy.svg
    :target: https://badge.fury.io/py/dialogy

Dialogy is a battries-included 🔋 opinionated framework to build machine-learning solutions for speech applications.

-   Plugin-based: Makes it easy to import/export components to other projects. 🔌
-   Stack-agnostic: No assumptions made on ML stack; your choice of machine learning library will not be affected by using Dialogy. 👍
-   Progressive: Minimal boilerplate writing to let you focus on your machine learning problems. 🤏

[Documentation](https://vernacular-ai.github.io/dialogy/)

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

Training boilerplate
*********************

❌. This is not an end-to-end automated model training framework. That said, no one wants to write boilerplate code,
unfortunately, it doesn't align with the objectives of this project. Also, it is hard to accomodate for different needs
like:

-   library dependencies
-   hardware support
-   Need for visualizations/reports during/after training.

Any rigidity here would lead to distractions both to maintainers and users of this project.
:ref:`Plugins<plugin>` and custom :ref:`Workflow<workflow>` are certainly welcome and can take care of recipe-based needs.
We already have a `dialogy-template-simple-transformers <https://github.com/Vernacular-ai/dialogy-template-simple-transformers>`_.

.. note:: Popular workflow sub-classes will be accepted after code-review.

Common Evaluation Plans
**************************

❌. Evaluation of models is hard to standardize. if you have a fairly common need, feel free to contribute your `workflow`, `plugins`.

Benefits
*********
-   ✅. This project offers a conduit for an untrained model. This means once a [Workflow](https://vernacular-ai.github.io/dialogy/dialogy/workflow/workflow.html) is ready you can use it anywhere:
    evaluation scripts, serving your models via an API, custom training/evaluation scripts, combining another workflow, etc.

-   ✅. If your application needs spoken language understanding, you should find little need to write data processing functions.

-   ✅. Little to no learning curve, if you know python you know how to use this project.

Contributions
--------------

-   Go through the docs.

-   Name your branch as "purpose/short-description". examples:
    -   "feature/hippos_can_fly"
    -   "fix/breathing_water_instead_of_fire"
    -   "docs/chapter_on_mighty_sphinx"
    -   "refactor/limbs_of_mummified_pharao"
    -   "test/my_patience"

-   Make sure tests are added are passing. Run `make test lint` at project root. Coverage is important aim for 100% unless reviewer agrees.

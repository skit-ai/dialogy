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

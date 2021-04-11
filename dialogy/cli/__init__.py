"""
This module exposes a command line utility to create project scaffolding. This creates a starting point for any project, an exhibit:

.. code-block:: bash
    :linenos:
    :emphasize-lines: 1

    dialogy create hello-world dialogy-template-simple-transformers
    cd hello-world
    poetry install
    make lint

Usage:
  __init__.py create <project> <template> [--namespace=<namespace>]

Options:

    <template>
        The source data directory; models, datasets, metrics will be copied from here.

    <project>
        A directory with this name will be created at the root of command invocation.

    --namespace=<namespace>
        The version of the dataset, model, metrics to use.

    -h --help
        Show this screen.

    --version
        Show current project version.
"""

from docopt import docopt  # type: ignore

from dialogy.cli.project import new_project


def main() -> None:
    """
    Create project scaffolding cli.
    """
    args = docopt(__doc__)
    project_name = args["<project>"]
    template_name = args["<template>"]
    namespace = args["--namespace"]

    if not namespace:
        new_project(project_name, template_name)
    else:
        new_project(project_name, template_name, namespace=namespace)

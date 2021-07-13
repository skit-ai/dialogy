"""
This module exposes a command line utility to create project scaffolding. This creates a starting point for any project, an exhibit:

.. code-block:: bash
    :linenos:
    :emphasize-lines: 1

    dialogy create hello-world
    cd hello-world
    poetry install
    make lint

Usage:
  __init__.py create <project>
  __init__.py create <project> <template> [--namespace=<namespace>] [--vcs=<vcs>]
  __init__.py update <project>
  __init__.py update <project> <template> [--namespace=<namespace>] [--vcs=<vcs>]

Options:

    <template>
        The source data directory; models, datasets, metrics will be copied from here.

    <project>
        A directory with this name will be created at the root of command invocation.

    --namespace=<namespace>
        The version of the dataset, model, metrics to use.

    --vcs=<vcs>
        accepts either "HEAD" or "TAG", "HEAD" refers to the latest git commit in the <template>
        "TAG" refers to the latest git release tag in <template>

    -h --help
        Show this screen.

    --version
        Show current project version.
"""
import os
from typing import Optional

from copier import copy  # type: ignore
from docopt import docopt  # type: ignore

from dialogy.cli.project import canonicalize_project_name
from dialogy.utils.logger import log


def project(
    destination_path: str,
    template: str = "dialogy-template-simple-transformers",
    namespace: str = "vernacular-ai",
    vcs_ref: Optional[str] = None,
    is_update: bool = False,
) -> None:
    """
    Create a new project using scaffolding from an existing template.

    This function uses `copier's <https://copier.readthedocs.io/en/stable/>`_ `copy <https://copier.readthedocs.io/en/stable/#quick-usage>`_ to use an existing template.

    An example template is `here: <https://github.com/Vernacular-ai/dialogy-template-simple-transformers>`_.

    :param destination_path: The directory where the scaffolding must be generated, creates a dir if missing but aborts if there are files already in the specified location.
    :type destination_path: str
    :param template: Scaffolding will be generated using a copier template project. This is the link to the project.
    :type template: str
    :param namespace: The user or the organization that supports the template, defaults to "vernacular-ai"
    :type namespace: str, optional
    :param vcs_ref: support for building from local git templates optionally, `--vcs` takes `"TAG"` or `"HEAD"`. defaults to `None`.
    :type vcs_ref: str, optional
    :return: None
    :rtype: NoneType
    """
    if not os.path.exists(destination_path):
        os.mkdir(destination_path)

    if os.listdir(destination_path) and not is_update:
        log.error("There are files on the destination path. Aborting !")
        return None

    # to handle copier vcs associated git template building.
    if vcs_ref is not None:
        if vcs_ref == "TAG":
            vcs_ref = None
        copy(
            template,
            destination_path,
            vcs_ref=vcs_ref,
            only_diff=is_update,
            force=is_update,
        )
    else:
        copy(
            f"gh:{namespace}/{template}.git",
            destination_path,
            only_diff=is_update,
            force=is_update,
        )

    return None


def main() -> None:
    """
    Create project scaffolding cli.
    """
    args = docopt(__doc__)
    project_name = args["<project>"]
    template_name = args["<template>"]
    namespace = args["--namespace"]
    vcs_ref = args["--vcs"]
    is_update = args["update"]

    if vcs_ref not in [None, "TAG", "HEAD"]:
        raise ValueError(
            f'--vcs expects either "HEAD" or "TAG" but was passed {vcs_ref}, \
            see more in --help'
        )

    template_name, namespace = canonicalize_project_name(template_name, namespace)
    project(
        project_name,
        template=template_name,
        namespace=namespace,
        vcs_ref=vcs_ref,
        is_update=is_update,
    )

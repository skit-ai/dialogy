"""
This module exposes a command line utility to create project scaffolding. This creates a starting point for any project, an exhibit:

.. code-block:: bash
    :linenos:
    :emphasize-lines: 1

    dialogy create hello-world
    cd hello-world
    poetry install
    make lint

usage: dialogy [-h] [--template TEMPLATE] [--namespace NAMESPACE] [--vcs {HEAD,TAG}] {create,update} project

positional arguments:
  {create,update}
  project               A directory with this name will be created at the root of command invocation.

optional arguments:
  -h, --help            show this help message and exit
  --template TEMPLATE
  --namespace NAMESPACE
                        The github/gitlab user or organization name where the template project lies.
  --vcs {HEAD,TAG}      Download the template's latest tag (TAG) or master branch (HEAD).
"""
import argparse
import os
import shutil
from typing import Optional

from copier import copy  # type: ignore

import dialogy.constants as const
from dialogy.utils.logger import logger


def project(
    destination_path: str,
    template: str = const.DEFAULT_PROJECT_TEMPLATE,
    namespace: str = const.DEFAULT_NAMESPACE,
    use_master: bool = False,
    pretend: bool = False,
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
    # to handle copier vcs associated git template building.
    if use_master:
        copy(
            template,
            destination_path,
            vcs_ref="HEAD",
            pretend=pretend,
            only_diff=is_update,
            force=is_update,
        )
    else:
        copy(
            f"gh:{namespace}/{template}.git",
            destination_path,
            only_diff=is_update,
            pretend=pretend,
            force=is_update,
        )

    return None


def add_project_command_arguments(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    parser.add_argument(
        "project",
        help="A directory with this name will be created at the root of command invocation.",
    )
    parser.add_argument("--template", default=const.DEFAULT_PROJECT_TEMPLATE)
    parser.add_argument(
        "--dry-run",
        help="Make no change to the directory structure.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--namespace",
        help="The github/gitlab user or organization name where the template project lies.",
        default=const.DEFAULT_NAMESPACE,
    )
    parser.add_argument(
        "--master",
        help="Download the template's master branch (HEAD) instead of the latest tag.",
        action="store_true",
    )
    return parser


def add_workflow_command_arguments(
    parser: argparse.ArgumentParser, objective: str
) -> argparse.ArgumentParser:
    parser.add_argument(
        "module", help="The module that contains a Workflow (or subclass)."
    )
    parser.add_argument("--workflow", help="The Workflow class.", default="Workflow")
    parser.add_argument(
        "--data",
        help=f"The dataset (.csv) to be use for {objective.lower()}ing the workflow.",
    )
    parser.add_argument(
        "--out",
        help="model",
        default="The directory where the artifacts must be stored.",
    )
    parser.add_argument(
        "--version",
        help="The version of the model to be used for {objective.lower()}ing the workflow.",
    )
    return parser


def project_command_parser(command_string: Optional[str]) -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser()

    parser = argument_parser.add_subparsers(
        help="Dialogy project utilities.", dest="command"
    )
    create_parser = parser.add_parser("create", help="Create a new project.")
    update_parser = parser.add_parser(
        "update", help="Migrate an existing project to the latest template version."
    )
    create_parser = add_project_command_arguments(create_parser)
    update_parser = add_project_command_arguments(update_parser)
    train_workflow_parser = parser.add_parser("train", help="Train a workflow.")
    test_workflow_parser = parser.add_parser("test", help="Test a workflow.")
    train_workflow_parser = add_workflow_command_arguments(
        train_workflow_parser, "train"
    )
    test_workflow_parser = add_workflow_command_arguments(test_workflow_parser, "test")

    command = command_string.split() if command_string else None
    return argument_parser.parse_args(args=command)


def main(command_string: Optional[str] = None) -> None:
    """
    Create project scaffolding cli.
    """
    args = project_command_parser(command_string)
    destination_path = project_name = args.project
    template_name = args.template
    namespace = args.namespace
    use_master = args.master
    is_update = args.command == "update"
    pretend = args.dry_run

    if os.path.exists(destination_path) and os.listdir(destination_path) and not is_update:
        raise RuntimeError("There are files on the destination path. Aborting !")

    if not os.path.exists(project_name):
        os.mkdir(destination_path)
        if pretend:
            shutil.rmtree(destination_path)

    project(
        project_name,
        template=template_name,
        namespace=namespace,
        use_master=use_master,
        is_update=is_update,
        pretend=pretend,
    )

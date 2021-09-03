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
from typing import Optional

import dialogy.constants as const
from dialogy.cli import project, workflow


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
    parser.add_argument(
        "--fn",
        help="A function that returns a Workflow or its subclass's instance.",
        required=True,
    )
    parser.add_argument(
        "--data",
        help=f"The dataset (.csv) to be use for {objective.lower()}ing the workflow.",
        required=True,
    )
    parser.add_argument(
        "--project",
        help=f"The project to be used for {objective.lower()}ing.",
        default="slu",
    )
    parser.add_argument(
        "--lang",
        help=f"The language expected for {objective.lower()}ing.",
        default="all",
    )
    return parser


def project_command_parser(command_string: Optional[str]) -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser()

    parser = argument_parser.add_subparsers(
        help="Dialogy project utilities.", dest="command"
    )
    create_parser = parser.add_parser(const.CREATE, help="Create a new project.")
    update_parser = parser.add_parser(
        const.UPDATE, help="Migrate an existing project to the latest template version."
    )
    create_parser = add_project_command_arguments(create_parser)
    update_parser = add_project_command_arguments(update_parser)
    train_workflow_parser = parser.add_parser(const.TRAIN, help="Train a workflow.")
    train_workflow_parser = add_workflow_command_arguments(
        train_workflow_parser, const.TRAIN
    )

    command = command_string.split() if command_string else None
    return argument_parser.parse_args(args=command)


def main(command_string: Optional[str] = None) -> None:
    """
    Create project scaffolding cli.
    """
    args = project_command_parser(command_string=command_string)
    if args.command in [const.CREATE, const.UPDATE]:
        project.project_cli(args)
    elif args.command in [const.TRAIN]:
        workflow.workflow_cli(args)

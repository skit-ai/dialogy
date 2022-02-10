import argparse
import importlib
from typing import Any

import pandas as pd
from loguru import logger

import dialogy.constants as const
from dialogy.workflow import Workflow


def get_workflow(
    module: str, get_workflow_fn: str, purpose: str, **kwargs: Any
) -> Workflow:
    return getattr(importlib.import_module(module), get_workflow_fn)(purpose, **kwargs)


def train_workflow(args: argparse.Namespace) -> None:
    """
    Train a workflow.
    """
    module = args.module
    get_workflow_fn = args.fn
    data = args.data
    lang = args.lang
    project = args.project
    kwargs = {"lang": lang, "project": project}

    workflow: Workflow = get_workflow(module, get_workflow_fn, args.command, **kwargs)
    train_df = pd.read_csv(data)
    try:
        workflow.train(train_df)
    except AttributeError as error:
        logger.error(f"{workflow=} doesn't have a train method? 🤔")
        raise AttributeError from error


def workflow_cli(args: argparse.Namespace) -> None:
    """
    CLI entry point for workflows.

    args contain the following attributes:

    module      - We expect the Workflow or its subclass to be available at this path.
    fn          - A function that provides a Workflow or its subclass' instance.
    data        - Path to dataset (.csv).
    output_dir  - Path where artifacts are expected.
    """
    command = args.command
    try:
        if command == const.TRAIN:
            train_workflow(args)
    except ModuleNotFoundError as error:
        logger.error(
            f"Could not import module {args.module} is "
            "your virtual environment active? 🤔.\n"
        )
        raise ModuleNotFoundError from error
    except AttributeError as error:
        logger.error(f"Could not find {args.fn} in {args.module}? 🤔.\n{error}")
        raise AttributeError from error

    return None

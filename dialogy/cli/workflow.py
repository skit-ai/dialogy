import argparse
import importlib

import pandas as pd
from sklearn.metrics import classification_report

import dialogy.constants as const
from dialogy.workflow import Workflow
from dialogy.utils import logger, create_timestamps_path


def train_workflow(args: argparse.Namespace) -> None:
    """
    Train a workflow.
    """
    module = args.module
    get_workflow_fn = args.fn
    data = args.data

    workflow: Workflow = getattr(importlib.import_module(module), get_workflow_fn)()
    train_df = pd.read_csv(data)
    try:
        workflow.train(train_df)
    except AttributeError as error:
        logger.error(f"{workflow=} doesn't have a train method? 🤔")
        raise AttributeError from error


def test_workflow(args: argparse.Namespace) -> None:
    """
    Test a workflow.
    """
    module = args.module
    get_workflow_fn = args.fn
    data = args.data
    output_dir = args.out
    join_id = args.join_id

    workflow: Workflow = getattr(importlib.import_module(module), get_workflow_fn)()
    test_df = pd.read_csv(data)
    try:
        result_df = workflow.prediction_labels(test_df, join_id)
    except AttributeError as error:
        logger.error(f"{workflow=} doesn't have a prediction_labels method? 🤔")
        raise AttributeError from error

    result_df = pd.merge(test_df, result_df, on=join_id)
    report = pd.DataFrame(classification_report(result_df[const.LABELS], result_df[const.INTENT], zero_division=0, output_dict=True)).T
    report.to_csv(create_timestamps_path(output_dir, "report.csv"), index=False)


def workflow_cli(args: argparse.Namespace) -> None:
    """
    CLI entry point for workflows.

    args contain the following attributes:
    ----

    module      - We expect the Workflow or its subclass to be available at this path.
    fn          - A function that provides a Workflow or its subclass' instance.
    data        - Path to dataset (.csv).
    output_dir  - Path where artifacts are expected.
    """
    command = args.command
    try:
        if command == const.TRAIN:
            train_workflow(args)
        elif command == const.TEST:
            test_workflow(args)
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

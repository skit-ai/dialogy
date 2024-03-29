import io
import os
import shutil
import tempfile

import pandas as pd
import pydantic
import pytest

import dialogy.constants as const
from dialogy import cli
from dialogy.cli import workflow


class MockWorkflow:
    def train(self, train_data):
        return

    def prediction_labels(self, test_df: pd.DataFrame, id_):
        report_df = test_df.copy()
        report_df.rename(columns={const.LABELS: const.INTENT}, inplace=True)
        report_df["score"] = 1.0
        report_df.drop("data", axis=1, inplace=True)
        return report_df


def get_workflow(purpose, **kwargs):
    return MockWorkflow()


def get_trash_workflow(purpose, **kwargs):
    return None


def test_project_creation_invalid():
    """Test an invalid command."""
    with pytest.raises(SystemExit):
        cli.main("unknown hello_world --dry-run")


def test_project_creation_safe_exit(monkeypatch):
    """Test the command to fail if destination is not empty."""
    monkeypatch.setattr("sys.stdin", io.StringIO("no"))
    directory = "hello_world"
    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(os.path.join(directory, "data"), exist_ok=True)

    try:
        cli.main(f"create {directory} --dry-run")
        if os.path.exists(directory):
            shutil.rmtree(directory)
        pytest.fail("Should have raised a RuntimeError.")
    except RuntimeError:
        if os.path.exists(directory):
            shutil.rmtree(directory)


def test_invalid_workflow_module():
    module = "this.module.is.invalid"
    func = "get_workflow"
    file_name = "doesntmatter.csv"
    with pytest.raises(ModuleNotFoundError):
        cli.main(f"train {module} --fn={func} --data={file_name}")


def test_invalid_workflow_function():
    module = "tests.cli.test_project"
    func = "invalid_fn"
    file_name = "doesntmatter.csv"
    with pytest.raises(AttributeError):
        cli.main(f"train {module} --fn={func} --data={file_name}")


def test_workflow_without_train_method():
    module = "tests.cli.test_project"
    func = "get_trash_workflow"
    _, file_name = tempfile.mkstemp(suffix=".csv")
    train_df = pd.DataFrame([{"data": "..."}])
    train_df.to_csv(file_name, index=False)
    with pytest.raises(AttributeError):
        cli.main(f"train {module} --fn={func} --data={file_name}")
    os.remove(file_name)


def test_workflow_train():
    """Test the command to train a model."""
    _, file_name = tempfile.mkstemp(suffix=".csv")
    module = "tests.cli.test_project"
    func = "get_workflow"
    train_df = pd.DataFrame([{"data": "..."}])
    train_df.to_csv(file_name, index=False)
    try:
        cli.main(f"train {module} --fn={func} --data={file_name}")
        os.remove(file_name)
    except (ModuleNotFoundError, AttributeError) as error:
        os.remove(file_name)
        pytest.fail(f"Workflow can't be extracted from {module}:{func}. {error}")

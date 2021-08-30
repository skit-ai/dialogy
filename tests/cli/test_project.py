from genericpath import exists
import os
import shutil
import io
import pydantic
import pytest
from dialogy import cli


def test_project_creation_invalid():
    """Test an invalid command."""
    with pytest.raises(SystemExit):
        cli.main("unknown hello_world --dry-run")


def test_project_creation_from_tag(monkeypatch):
    """Test a valid command to build from latest tag."""
    monkeypatch.setattr("sys.stdin", io.StringIO("no"))
    try:
        cli.main("create hello_world --dry-run")
    except SystemExit:
        pytest.fail("Unexpected SystemExit")


def test_project_creation_from_master(monkeypatch):
    """Test a valid command to build from master branch."""
    monkeypatch.setattr("sys.stdin", io.StringIO("no"))
    with pytest.raises(pydantic.ValidationError):
        cli.main("create hello_world --dry-run --master")


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

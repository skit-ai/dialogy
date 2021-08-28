import json
import os
import tempfile

from dialogy.utils.file_handler import load_file


def test_load_file_json():
    data = {"a": "b"}
    _, file_path = tempfile.mkstemp(suffix=".json")
    with open(file_path, "w") as f:
        json.dump(data, f)
    assert load_file(file_path, loader=json.load) == data
    os.remove(file_path)


def test_missing_file_path():
    assert load_file(None, loader=json.load) is None


def test_load_file_file():
    data = ""
    _, file_path = tempfile.mkstemp(suffix=".txt")
    with open(file_path, "w") as f:
        f.write(data)
    assert load_file(file_path) == data
    os.remove(file_path)

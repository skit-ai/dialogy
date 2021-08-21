import json
import os
import tempfile

from dialogy.utils.file_handler import safe_load


def test_safe_load_json():
    data = {"a": "b"}
    _, file_path = tempfile.mkstemp(suffix=".json")
    with open(file_path, "w") as f:
        json.dump(data, f)
    assert safe_load(file_path, loader=json.load) == data
    os.remove(file_path)


def test_missing_file_path():
    assert safe_load(None, loader=json.load) is None


def test_safe_load_file():
    data = ""
    _, file_path = tempfile.mkstemp(suffix=".txt")
    with open(file_path, "w") as f:
        f.write(data)
    assert safe_load(file_path) == data
    os.remove(file_path)

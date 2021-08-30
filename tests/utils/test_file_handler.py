import json
import os
import pickle
import tempfile
from datetime import datetime

from dialogy.utils.file_handler import load_file, save_file, create_timestamps_path


def test_load_file_json():
    data = {"a": "b"}
    _, file_path = tempfile.mkstemp(suffix=".json")
    save_file(file_path, data, writer=json.dump)
    assert load_file(file_path, loader=json.load) == data
    os.remove(file_path)


def test_missing_file_path():
    assert load_file(None, loader=json.load) is None


def test_load_file_default_file():
    data = ""
    _, file_path = tempfile.mkstemp(suffix=".txt")
    with open(file_path, "w") as f:
        f.write(data)
    assert load_file(file_path) == data
    os.remove(file_path)


def test_save_binary_file():
    data = b"apples"
    _, file_path = tempfile.mkstemp(suffix=".json")
    save_file(file_path, data, mode="wb", writer=pickle.dump)
    assert load_file(file_path, mode="rb", loader=pickle.load) == data
    os.remove(file_path)


def test_save_file_no_path():
    assert save_file(None) is None


def test_create_timestamps_path():
    timestamp = datetime.now()
    directory = "hello-world"
    file_name = "some.csv"
    path = os.path.join(directory, timestamp.strftime("%d-%B-%Y"), timestamp.strftime("%H-%M-%S-%f"), file_name)
    assert create_timestamps_path(directory, file_name, timestamp=timestamp, dry_run=True) == path

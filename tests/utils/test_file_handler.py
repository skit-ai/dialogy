import json
import os
import pickle
import shutil
import tempfile
from datetime import datetime

from dialogy.utils.file_handler import (create_timestamps_path, load_file,
                                        read_from_json, save_file,
                                        save_to_json)


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
    path = os.path.join(
        directory,
        timestamp.strftime("%d-%B-%Y"),
        timestamp.strftime("%H-%M-%S-%f"),
        file_name,
    )
    assert (
        create_timestamps_path(directory, file_name, timestamp=timestamp, dry_run=True)
        == path
    )


def test_create_timestamps_path_real_run():
    timestamp = datetime.now()
    directory = "hello-world"
    file_name = "some.csv"
    dir_path = os.path.join(
        directory,
        timestamp.strftime("%d-%B-%Y"),
        timestamp.strftime("%H-%M-%S-%f"),
    )
    path_ = os.path.join(dir_path, file_name)
    produced_path = create_timestamps_path(
        directory, file_name, timestamp=timestamp, dry_run=False
    )
    shutil.rmtree(dir_path)
    assert produced_path == path_


def test_read_from_json():
    empty_config = read_from_json(["a", "b"], "/tmp", "fake.json")
    assert isinstance(empty_config, dict)
    assert empty_config == {}
    fake_config = {"a": 1, "b": [1, 2]}
    _, file_path = tempfile.mkstemp(suffix=".json")
    dir, file_name = os.path.split(file_path)
    with open(file_path, "w") as f:
        json.dump(fake_config, f)
    assert list(read_from_json(["a", "b"], dir, file_name).items()) == list(
        fake_config.items()
    )
    os.remove(file_path)


def test_save_to_json_empty_config():
    fake_config = {"a": 1, "b": [1, 2]}
    _, file_path = tempfile.mkstemp(suffix=".json")
    dir, file_name = os.path.split(file_path)
    save_to_json(fake_config, dir, file_name)
    with open(file_path, "r") as f:
        assert list(json.load(f).items()) == list(fake_config.items())
    os.remove(file_path)


def test_save_to_json_filled_config():
    old_config = {"a": 1, "b": [1, 2]}
    new_config = {"a": 2, "b": [3, 4]}
    _, file_path = tempfile.mkstemp(suffix=".json")
    with open(file_path, "w") as f:
        json.dump(old_config, f)
    dir, file_name = os.path.split(file_path)
    save_to_json(new_config, dir, file_name)
    with open(file_path, "r") as f:
        assert list(json.load(f).items()) == list(new_config.items())
    os.remove(file_path)

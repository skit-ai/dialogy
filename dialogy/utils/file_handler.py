import json
import os
from datetime import datetime
from json.decoder import JSONDecodeError
from typing import Any, Dict, List, Optional

from loguru import logger


def load_file(
    file_path: Optional[str] = None, mode: str = "r", loader: Any = None
) -> Any:
    """
    Safely load a file.

    :param file_path: The path to the file to load.
    :type file_path: [type]
    :param mode: The mode to use when opening the file., defaults to "r"
    :type mode: str, optional
    :return: The file contents.
    :rtype: Any
    """
    if not isinstance(file_path, str):
        return None

    if os.path.exists(file_path):
        with open(file_path, mode) as file:
            if not loader:
                return file.read()
            else:
                return loader(file)
    else:
        return None  # pragma: no cover


def save_file(
    file_path: Optional[str] = None,
    content: Any = None,
    mode: str = "w",
    encoding: str = "utf-8",
    newline: str = "\n",
    writer: Any = None,
) -> None:
    """
    Save a file.

    :param file_path: The path to the file to save.
    :type file_path: str
    :param content: The content to save.
    :type content: Any
    :param mode: The mode to use when opening the file., defaults to "w"
    :type mode: str, optional
    :param encoding: The encoding to use when writing the file, defaults to "utf-8"
    :type encoding: str, optional
    :param newline: The newline character to use when writing the file, defaults to "\n"
    :type newline: str, optional
    """
    if not isinstance(file_path, str):
        return None

    if mode == "wb":
        with open(file_path, mode) as file:
            _ = file.write(content) if not writer else writer(content, file)
    else:
        with open(file_path, mode, encoding=encoding, newline=newline) as file:
            _ = file.write(content) if not writer else writer(content, file)


def read_from_json(params: List[str], dir_path: str, file_name: str) -> Dict[str, Any]:
    full_path = os.path.join(dir_path, file_name)
    req_config = {}
    if os.path.exists(full_path):
        with open(full_path, "r") as json_file:
            config_ = json.load(json_file)
            req_config = {param: config_.get(param) for param in params}
    return req_config


def save_to_json(params: Dict[str, Any], dir_path: str, file_name: str) -> None:
    full_path = os.path.join(dir_path, file_name)
    existing_config = {}
    if os.path.exists(full_path):
        try:
            with open(full_path, "r") as json_file:
                existing_config = json.load(json_file)
                for key, val in params.items():
                    existing_config[key] = val
        except JSONDecodeError:
            logger.error(
                f"Failed to load json file {full_path}, writing on newly created file."
            )
    params = existing_config or params
    with open(full_path, "w") as json_file:
        json.dump(params, json_file, indent=1, ensure_ascii=False)


def create_timestamps_path(
    directory: str,
    file_name: str,
    timestamp: Optional[datetime] = None,
    dry_run: bool = False,
) -> str:
    timestamp = timestamp or datetime.now()
    dir_path = os.path.join(
        directory, timestamp.strftime("%d-%B-%Y"), timestamp.strftime("%H-%M-%S-%f")
    )
    if not dry_run:
        os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, file_name)

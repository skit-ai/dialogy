import os
from datetime import datetime
from typing import Any, Optional


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
        return None


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

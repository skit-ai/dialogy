import os
from typing import Any, Optional


def safe_load(
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

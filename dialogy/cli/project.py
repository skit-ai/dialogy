"""
This module offers utilities to create a new project from a given template.
"""
import os

from copier import copy  # type: ignore

from dialogy.utils.logger import log


def new_project(
    destination_path: str, template: str, namespace: str = "vernacular-ai"
) -> None:
    """
    Create project scaffolding.

    This function uses [`copier.copy`](https://copier.readthedocs.io/en/stable/)
    to use an existing template.

    Args:
        template (str):
            Look for "dialogy-template-*" here:  https://github.com/Vernacular-ai
            Example: "dialogy-template-simple-transformers"
        destination_path (str):
        namespace (str, optional): A github/gitlab Organization or Username. Defaults to "vernacular-ai".
    """
    if not os.path.exists(destination_path):
        os.mkdir(destination_path)

    if os.listdir(destination_path):
        log.error("There are files on the destination path. Aborting !")
        return None

    copy(f"gh:{namespace}/{template}.git", destination_path)
    return None

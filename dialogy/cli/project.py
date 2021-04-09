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
    Create a new project using scaffolding from an existing template.

    This function uses `copier's <https://copier.readthedocs.io/en/stable/>`_ `copy <https://copier.readthedocs.io/en/stable/#quick-usage>`_ to use an existing template.

    An example template is `here: <https://github.com/Vernacular-ai/dialogy-template-simple-transformers>`_.

    :param destination_path: The directory where the scaffolding must be generated, creates a dir if missing but aborts if there are files already in the specified location.
    :type destination_path: str
    :param template: Scaffolding will be generated using a copier template project. This is the link to the project.
    :type template: str
    :param namespace: The user or the organization that supports the template, defaults to "vernacular-ai"
    :type namespace: str, optional
    :return: None
    :rtype: NoneType
    """
    if not os.path.exists(destination_path):
        os.mkdir(destination_path)

    if os.listdir(destination_path):
        log.error("There are files on the destination path. Aborting !")
        return None

    copy(f"gh:{namespace}/{template}.git", destination_path)
    return None

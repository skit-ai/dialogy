"""
This module offers utilities to create a new project from a given template.
"""
from copier import copy  # type: ignore


def new_project(
    template: str, destination_path: str, namespace: str = "vernacular-ai"
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
    copy(f"gh:{namespace}/{template}.git", destination_path)

from typing import Optional, Tuple

DEFAULT_NAMESPACE = "vernacular-ai"
DEFAULT_PROJECT_TEMPLATE = "dialogy-template-simple-transformers"


def canonicalize_project_name(
    template: Optional[str] = None, namespace: Optional[str] = None
) -> Tuple[str, str]:
    """
    :param template: Scaffolding will be generated using a copier template project. This is the link to the project.
    :type template: str
    :param namespace: The user or the organization that supports the template, defaults to "vernacular-ai"
    :type namespace: str, optional
    :return: None
    :rtype: NoneType
    """
    template = template or DEFAULT_PROJECT_TEMPLATE
    namespace = namespace or DEFAULT_NAMESPACE
    return template, namespace

from dialogy.cli.project import (
    DEFAULT_NAMESPACE,
    DEFAULT_PROJECT_TEMPLATE,
    canonicalize_project_name,
)


def test_canonicalize_project_name_missing_template():
    assert canonicalize_project_name(namespace="apples") == (
        DEFAULT_PROJECT_TEMPLATE,
        "apples",
    )


def test_canonicalize_project_name_missing_namespace():
    assert canonicalize_project_name(template="template") == (
        "template",
        DEFAULT_NAMESPACE,
    )


def test_canonicalize_project_name():
    assert canonicalize_project_name(template="template", namespace="apples") == (
        "template",
        "apples",
    )

import argparse
import os
import shutil

from copier import copy

import dialogy.constants as const


def manage_project(
    destination_path: str,
    template: str = const.DEFAULT_PROJECT_TEMPLATE,
    namespace: str = const.DEFAULT_NAMESPACE,
    use_master: bool = False,
    pretend: bool = False,
    is_update: bool = False,
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
    :param vcs_ref: support for building from local git templates optionally, `--vcs` takes `"TAG"` or `"HEAD"`. defaults to `None`.
    :type vcs_ref: str, optional
    :return: None
    :rtype: NoneType
    """
    # to handle copier vcs associated git template building.
    if use_master:
        copy(
            template,
            destination_path,
            vcs_ref="HEAD",
            pretend=pretend,
            only_diff=is_update,
            force=is_update,
        )
    else:
        copy(
            f"gh:{namespace}/{template}.git",
            destination_path,
            only_diff=is_update,
            pretend=pretend,
            force=is_update,
        )

    return None


def project_cli(args: argparse.Namespace) -> None:
    """CLI for project command."""
    destination_path = project_name = args.project
    template_name = args.template
    namespace = args.namespace
    use_master = args.master
    is_update = args.command == "update"
    pretend = args.dry_run

    if (
        os.path.exists(destination_path)
        and os.listdir(destination_path)
        and not is_update
    ):
        raise RuntimeError("There are files on the destination path. Aborting !")

    if not os.path.exists(project_name):
        os.mkdir(destination_path)
        if pretend:
            shutil.rmtree(destination_path)

    manage_project(
        project_name,
        template=template_name,
        namespace=namespace,
        use_master=use_master,
        is_update=is_update,
        pretend=pretend,
    )

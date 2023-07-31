"""
[summary]
"""
# type: ignore
import os
from typing import Any, Dict, List, Optional, Set, Union

import attr
import yaml
import glob
from loguru import logger
import traceback
import sys

import dialogy.constants as const
from dialogy.utils.misc import traverse_dict



class BaseConfig:
    def get(self, attribute: str) -> Any:
        # handles nested attributes
        if "." in attribute:
            levels = attribute.split(".")
            first, rest = levels[0], ".".join(levels[1:])
            first_accessed_val = vars(self).get(first)
            if isinstance(first_accessed_val, dict):
                key_list = rest.split(".")
                return traverse_dict(first_accessed_val, key_list)
            elif isinstance(first_accessed_val, BaseConfig):
                return first_accessed_val.get(rest)
            else:
                raise ValueError(f"Fetching {attribute} from config failed.")
        else:
            return vars(self).get(attribute)


@attr.s
class Task(BaseConfig):
    use = attr.ib(
        type=bool, kw_only=True, validator=attr.validators.instance_of(bool)
    )
    threshold = attr.ib(
        type=float, kw_only=True, validator=attr.validators.instance_of(float)
    )
    model_args = attr.ib(
        type=Dict[Any, Any], kw_only=True, validator=attr.validators.instance_of(dict)
    )
    alias = attr.ib(
        type=Dict[Any, Any],
        factory=dict, kw_only=True, validator=attr.validators.instance_of(dict)
    )
    skip = attr.ib(
        type=List[Any],
        factory=list, kw_only=True, validator=attr.validators.instance_of(list)
    )
    confidence_levels = attr.ib(
        type=List[Any],
        factory=list, kw_only=True, validator=attr.validators.instance_of(list)
    )
    format = attr.ib(
        type=str,
        factory=str,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def update_paths(self, project_config_path: str) -> None:
        for purpose in self.model_args:
            purpose_args = self.model_args[purpose]
            purpose_args[const.BEST_MODEL_DIR] = os.path.join(
                project_config_path, purpose_args[const.BEST_MODEL]
            )
            purpose_args[const.OUTPUT_DIR] = os.path.join(
                project_config_path, purpose_args[const.OUTPUT_DIR]
            )


@attr.s
class Tasks(BaseConfig):
    classification = attr.ib(
        type=Task, kw_only=True, validator=attr.validators.instance_of(dict)
    )

    def __attrs_post_init__(self) -> None:
        self.classification = Task(**self.classification)  # type: ignore

    def update_paths(self, project_path: str) -> None:
        self.classification.update_paths(project_path)


@attr.s
class PipelineConfig(BaseConfig):
    model_name = attr.ib(
        type=str, kw_only=True, validator=attr.validators.instance_of(str)
    )
    languages = attr.ib(type=List[str], kw_only=True)
    critical_intents = attr.ib(factory=list, type=List[str], kw_only=True)
    parsers = attr.ib(factory=list, type=List[Dict[str, str]], kw_only=True)
    pipeline_order = attr.ib(factory=list, type=List[str], kw_only=True)
    lang_locale_map = attr.ib(factory=dict, type=Dict[str, str], kw_only=True)


@attr.s
class ModelConfig(BaseConfig):
    tasks = attr.ib(type=Tasks, kw_only=True)

    def __attrs_post_init__(self) -> None:
        self.tasks = Tasks(**self.tasks)  # type: ignore

    def update_paths(self, project_path: str) -> None:
        self.tasks.update_paths(project_path)

    @staticmethod
    def _get_data_dir(task_name: str) -> str:
        return os.path.join(const.DATA, task_name)

    def get_model_dir(self, task_name: str) -> str:
        return os.path.join(self._get_data_dir(task_name), const.MODELS)


@attr.s
class CorePluginsConfig(BaseConfig):
    slots: Dict[str, Dict[str, Any]] = attr.ib(factory=dict, kw_only=True)
    calibration = attr.ib(factory=dict, type=Dict[str, Any], kw_only=True)
    entity_patterns = attr.ib(factory=dict, type=Dict[str, List[str]], kw_only=True)
    datetime_rules = attr.ib(
        factory=dict, type=Dict[str, Dict[str, Dict[str, int]]], kw_only=True
    )
    timerange_constraints = attr.ib(
        factory=dict, type=Dict[str, Dict[str, Dict[str, Dict[str, int]]]], kw_only=True
    )
    error_recovery = attr.ib(factory=list, type=List[str], kw_only=True)


# TODO: Fix getter methods here
@attr.s
class Config(BaseConfig):
    """
    An instance of config handles `config/config.yaml` configurations. This includes reading other related files, models, datasets, etc.

    An instance can:

    - Read config.yaml
    - Modify config.yaml
    - Load models and their configurations
    - Save pickled objects.
    """

    project_artifacts_root_path = attr.ib(type=str, kw_only=True)
    pipeline_config = attr.ib(type=PipelineConfig, kw_only=True)
    core_plugins_config = attr.ib(type=CorePluginsConfig, kw_only=True)
    model_config = attr.ib(type=ModelConfig, kw_only=True)
    misc_config = attr.ib(factory=dict, type=Dict[str, Any], kw_only=True)

    def __attrs_post_init__(self) -> None:
        self.pipeline_config = PipelineConfig(**self.pipeline_config) # type: ignore
        self.core_plugins_config = CorePluginsConfig(**self.core_plugins_config) # type: ignore
        self.model_config = ModelConfig(**self.model_config) # type: ignore
        self.update_paths()

    def update_paths(self) -> None:
        self.model_config.update_paths(self.project_artifacts_root_path)

    @staticmethod
    def _get_data_dir(task_name: str) -> str:
        return os.path.join(const.DATA, task_name)

    def get_metrics_dir(self, task_name: str) -> str:
        return os.path.join(
            self.project_artifacts_root_path,
            self._get_data_dir(task_name),
            const.METRICS,
        )

    def get_dataset_dir(self, task_name: str) -> str:
        return os.path.join(self.project_artifacts_root_path, self._get_data_dir(task_name), const.DATASETS)
    
    def get_model_dir(self, task_name: str) -> str:
        return os.path.join(
            self.project_artifacts_root_path,
            self.model_config.get_model_dir(task_name)
        )

    def get_skip_list(self, task_name: str) -> Set[str]:
        if task_name == const.CLASSIFICATION:
            return set(self.model_config.tasks.classification.skip)
        raise NotImplementedError(f"Model for {task_name} is not defined!")

    def get_dataset(self, task_name: str, file_name: str) -> Any:
        return os.path.join(
            self.project_artifacts_root_path,
            self._get_data_dir(task_name),
            const.DATASETS,
            file_name,
        )

    def get_model_args(self, task_name: str, purpose: str, **kwargs: Any) -> Dict[str, Any]:
        if task_name == const.CLASSIFICATION:
            args_map = self.model_config.tasks.classification.model_args
            if purpose == const.TRAIN:
                if epochs := kwargs.get(const.EPOCHS):
                    args_map[const.TRAIN][const.NUM_TRAIN_EPOCHS] = epochs
            return args_map
        raise NotImplementedError(f"Model for {task_name} is not defined!")

    def get_model_confidence_threshold(self, task_name: str) -> float:
        if task_name == const.CLASSIFICATION:
            return self.model_config.tasks.classification.threshold
        raise NotImplementedError(f"Model for {task_name} is not defined!")

    def get_supported_languages(self) -> List[str]:
        return self.pipeline_config.languages

    def get_locale_for_lang(self, lang: str) -> Optional[str]:
        return self.pipeline_config.lang_locale_map.get(lang)

    def json(self) -> Dict[str, Any]:
        """
        Represent the class as json

        :return: The class instance as json
        :rtype: Dict[str, Any]
        """
        return attr.asdict(self)

    def save(self) -> None:
        with open(os.path.join("config", "config.yaml"), "w") as handle:
            yaml.dump(self.json(), handle, allow_unicode=True)


def resolve_expressions(config: Config) -> Config:
    for index, parser in enumerate(config.pipeline_config.parsers):
        for key, value in parser.items():
            if isinstance(value, str):
                value = value.replace("\n", "")
                if value.startswith("{{") and value.endswith("}}"):
                    # python expression detected
                    value = eval(value[2:-2])
            if isinstance(value, dict): # type: ignore
                if "fetch_from_config" in value.keys(): # type: ignore
                    if isinstance(value["fetch_from_config"], str):
                        resolved_value = config.get(value["fetch_from_config"])
                        if resolved_value is None:
                            logger.error(
                                f"Value fetched for "
                                f"{value['fetch_from_config']} "
                                f"resolves to {resolved_value}"
                            )
                        value = resolved_value
            parser[key] = value
        config.pipeline_config.parsers[index] = parser
    return config


def get_project_artifacts_path_by_name(project_name: str, project_artifacts_root: str) -> str:
    return os.path.join(project_artifacts_root, project_name, "configs")


def fetch_project_config(project: str, all_project_artifacts_root: str) -> Optional[Config]:
    project_config_path = get_project_artifacts_path_by_name(
        project, all_project_artifacts_root
    )
    pipeline_config, core_plugins_config, model_config, misc_config = None, None, {}, {}
    for file in glob.glob(os.path.join(project_config_path, "*.yaml")):
        with open(file, "r", encoding="utf8") as handle:
            yaml_contents = yaml.safe_load(handle)
        if const.PIPELINE_CONFIG_FILE in file:
            pipeline_config = yaml_contents
        elif const.CORE_PLUGINS_CONFIG_FILE in file:
            core_plugins_config = yaml_contents
        elif const.MODEL_CONFIG_FILE in file:
            model_config = yaml_contents
        else:
            misc_config.update(yaml_contents)
    if pipeline_config is None or core_plugins_config is None or not model_config:
        raise RuntimeError("One of pipeline config, core_plugins_config or model "
                           "config is not found. Config for this project won't "
                           "be loaded")
    # TODO: raise exception for both kind of configs not found
    config = Config(
        **{ # type: ignore
            "project_artifacts_root_path": os.path.join(
                all_project_artifacts_root, project
            ),
            "pipeline_config": pipeline_config,
            "core_plugins_config": core_plugins_config,
            "model_config": model_config,
            "misc_config": misc_config,
        }
    )
    config = resolve_expressions(config)
    return config


def read_project_configs(
    project_artifacts_root: str, filter_list: Optional[List[str]] = None
) -> Dict[str, Config]:
    # TODO: raise exception if root is empty
    all_project_configs = {}
    # logger.enable("dialogy")
    logger.debug(f"Loading configs from {project_artifacts_root}")
    for project in os.listdir(project_artifacts_root):
        # hidden files from editors / OS like .idea
        if project.startswith("."):
            continue
        if filter_list and project not in filter_list:
            continue
        logger.debug(f"Loading config for {project}")
        config = None
        try:
            config = fetch_project_config(project, project_artifacts_root)
        except Exception as e:
            traceback.print_exception(*sys.exc_info())
            logger.debug(f"Failed to load config for {project}")
        if not config:
            continue
        all_project_configs.update({project: config})
    # logger.disable("dialogy")
    return all_project_configs

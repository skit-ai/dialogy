from functools import wraps
from typing import Any, Callable, Dict, Optional

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity


class EntityDeserializer:
    entitiy_classes: Dict[str, BaseEntity] = {}

    @classmethod
    def register(cls, dim: str) -> Callable[[Any], Any]:
        @wraps(cls)
        def decorator(entity_class: BaseEntity) -> BaseEntity:
            cls.entitiy_classes[dim] = entity_class
            return entity_class

        return decorator

    @classmethod
    def validate(cls, duckling_entity_dict: Dict[str, Any]) -> None:
        keys = tuple(sorted(duckling_entity_dict.keys()))
        if keys != const.DUCKLING_ENTITY_KEYS:
            raise ValueError(
                f"Invalid Duckling entity keys: {keys} expected {const.DUCKLING_ENTITY_KEYS}."
            )

        dimension = cls.get_dimension(duckling_entity_dict)
        if dimension not in const.DUCKLING_DIMS:
            raise ValueError(
                f"Invalid Duckling dimension: {dimension} expected {const.DUCKLING_DIMS}."
            )

    @staticmethod
    def get_keys_in_value_as_str(duckling_entity_dict: Dict[str, Any]) -> str:
        return " ".join(sorted(duckling_entity_dict[const.VALUE].keys()))

    @staticmethod
    def get_dimension(duckling_entity_dict: Dict[str, Any]) -> str:
        return duckling_entity_dict[const.DIM]

    @classmethod
    def get_entity_class_str(cls, duckling_entity_dict: Dict[str, Any]) -> str:
        return (
            const.TIME_INTERVAL
            if cls.get_keys_in_value_as_str(duckling_entity_dict)
            in const.DUCKLING_TIME_INTERVAL_ENTITY_KEYS
            else cls.get_dimension(duckling_entity_dict)
        )

    @classmethod
    def deserialize_duckling(
        cls,
        duckling_entity_dict: Dict[str, Any],
        alternative_index: int,
        reference_time: Optional[int] = None,
        timezone: str = "UTC",
        duration_cast_operator: Optional[str] = None,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> BaseEntity:
        cls.validate(duckling_entity_dict)
        entity_class_name = cls.get_entity_class_str(duckling_entity_dict)
        EntityClass: BaseEntity = cls.entitiy_classes[entity_class_name]

        try:
            entity = EntityClass.from_duckling(
                duckling_entity_dict,
                alternative_index,
                constraints=constraints,
                duration_cast_operator=duration_cast_operator,
                timezone=timezone,
                reference_time=reference_time,
            )
        except KeyError as e:
            raise ValueError(
                f"Failed to deserialize {EntityClass} "
                f"from duckling response: {duckling_entity_dict}. Exception: {e}"
            ) from e

        return entity

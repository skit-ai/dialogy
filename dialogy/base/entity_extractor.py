import operator
from typing import Any, Dict, List, Optional, Tuple

from pydash import py_  # type: ignore

from dialogy.base.plugin import Plugin, PluginFn
from dialogy.types.entity import BaseEntity


class EntityExtractor(Plugin):
    FUTURE = "future"
    PAST = "past"
    DATETIME_OPERATION_ALIAS = {FUTURE: operator.ge, PAST: operator.le}

    def __init__(
        self,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        debug: bool = False,
        threshold: Optional[float] = None,
    ) -> None:
        super().__init__(access, mutate, debug=debug)
        self.threshold = threshold

    def remove_low_scoring_entities(
        self, entities: List[BaseEntity]
    ) -> List[BaseEntity]:
        """
        Remove entities with a lower score than the threshold.

        :param entities: A list of entities.
        :type entities: List[BaseEntity]
        :return: A list of entities with score higher than configured threshold.
        :rtype: List[BaseEntity]
        """
        if self.threshold is None:
            return entities

        high_scoring_entities = []
        for entity in entities:
            if entity.score is None:
                high_scoring_entities.append(entity)

            if entity.score is not None and self.threshold < entity.score:
                high_scoring_entities.append(entity)

        return high_scoring_entities

    @staticmethod
    def entity_scoring(presence: int, input_size: int) -> float:
        return presence / input_size

    @staticmethod
    def aggregate_entities(
        entity_type_value_group: Dict[Tuple[str, Any], List[BaseEntity]],
        input_size: int,
    ) -> List[BaseEntity]:
        """
        Reduce entities sharing same type and value.

        Entities with same type and value are considered identical even if other metadata is same.

        :param entity_type_val_group: A data-structure that groups entities by type and value.
        :type entity_type_val_group: Dict[Tuple[str, Any], List[BaseEntity]]
        :return: A list of de-duplicated entities.
        :rtype: List[BaseEntity]
        """
        aggregated_entities = []
        for entities in entity_type_value_group.values():
            indices = [entity.alternative_index for entity in entities]
            min_alternative_index = py_.min_(indices)
            representative = entities[0]
            representative.alternative_index = min_alternative_index
            representative.score = EntityExtractor.entity_scoring(
                len(py_.uniq(indices)), input_size
            )
            aggregated_entities.append(representative)
        return aggregated_entities

    def apply_filters(self, entities: List[BaseEntity]) -> List[BaseEntity]:
        """
        Conditionally remove entities.

        :param entities: A list of entities.
        :type entities: List[BaseEntity]
        :return: A list of entities. This can be at most the same length as `entities`.
        :rtype: List[BaseEntity]
        """
        return self.remove_low_scoring_entities(entities)

    def entity_consensus(
        self, entities: List[BaseEntity], input_size: int
    ) -> List[BaseEntity]:
        """
        Combine entities by type and value.

        This issue:
        https://github.com/Vernacular-ai/dialogy/issues/52
        Points at the problems where we can return multiple identical entities,
        depending on the number of transcripts that contain same body.

        :param entities: A list of entities which may have duplicates.
        :type entities: List[BaseEntity]
        :return: A list of entities scored and unique by type and value.
        :rtype: List[BaseEntity]
        """
        entity_type_value_group = py_.group_by(
            entities, lambda entity: (entity.type, entity.get_value())
        )
        aggregate_entities = EntityExtractor.aggregate_entities(
            entity_type_value_group, input_size
        )
        return self.apply_filters(aggregate_entities)

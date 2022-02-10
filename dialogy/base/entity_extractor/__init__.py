import json
from typing import Any, Dict, List, Optional, Tuple

from pydash import py_

from dialogy.types import BaseEntity
from dialogy.utils import normalize


def entity_scoring(presence: int, input_size: int) -> float:
    return presence / input_size


class EntityScoringMixin:
    """
    Mixin for scoring and aggregation of entities over a set of transcripts.

    .. _EntityScoringMixin:
    """

    threshold: Optional[float] = None
    """
    Value to compare against an entity's score.
    """

    def remove_low_scoring_entities(
        self, entities: List[BaseEntity]
    ) -> List[BaseEntity]:
        """
        Remove entities with a lower score than the threshold.

        This doesn't apply to entities with score=None.

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

    def aggregate_entities(
        self,
        entity_type_value_group: Dict[Tuple[str, Any], List[BaseEntity]],
        input_size: int,
    ) -> List[BaseEntity]:
        """
        Reduce entities sharing same type and value.

        - Entities with same type and value are considered identical even if other metadata is same.
          These entities are part of a group.
        - We track the transcript indices for every entity in a group.
        - Select the minimum of all the indices. (because 0th transcript has highest confidence)
        - We pick one entity per group and modify its index to the minimum and score is aggregated for the group.
        - The entity picked is added to a list of aggregates.

        The above is done for all entities in a group

        :param entity_type_val_group: A data-structure that groups entities by type and value.
        :type entity_type_val_group: Dict[Tuple[str, Any], List[BaseEntity]]
        :return: A list of de-duplicated entities.
        :rtype: List[BaseEntity]
        """
        aggregated_entities = []
        for entities in entity_type_value_group.values():
            indices = [
                entity.alternative_index
                for entity in entities
                if isinstance(entity.alternative_index, int)
            ]
            min_alternative_index = py_.min_(indices) if indices else None
            representative = entities[0]
            representative.alternative_index = min_alternative_index
            representative.alternative_indices = indices
            representative.score = entity_scoring(len(py_.uniq(indices)), input_size)
            aggregated_entities.append(representative)
        return aggregated_entities

    def apply_filters(self, entities: List[BaseEntity]) -> List[BaseEntity]:
        """
        Filter entities with score less than the threshold.

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
        aggregate_entities = self.aggregate_entities(
            entity_type_value_group, input_size
        )
        return self.apply_filters(aggregate_entities)

    @staticmethod
    def make_transform_values(transcript: Any) -> List[str]:
        """
        Make transcripts from a string/json-string.

        :param transcript: A string to search entities within.
        :type transcript: str
        :return: List of transcripts.
        :rtype: List[str]
        """
        try:
            transcript = json.loads(transcript)
            return normalize(transcript)
        except (json.JSONDecodeError, TypeError):
            return normalize(transcript)

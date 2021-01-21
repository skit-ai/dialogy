"""Module provides access to entity types. 

Import functions:
    - entity_synthesis

Import classes:
    - BaseEntity
    - NumericalEntity,
    - PeopleEntity,
    - TimeEntity,
    - TimeIntervalEntity
    - LocationEntity
"""

from dialogy.types.entities.base_entities import BaseEntity, entity_synthesis
from dialogy.types.entities.numerical_entities import (
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
)
from dialogy.types.entities.location_entities import LocationEntity

dimension_entity_map = {
    "number": {"value": NumericalEntity},
    "people": {"value": PeopleEntity},
    "time": {"value": TimeEntity, "interval": TimeIntervalEntity},
}

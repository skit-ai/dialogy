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

from dialogy.types.entity.base_entity import BaseEntity, entity_synthesis
from dialogy.types.entity.numerical_entity import (
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
)
from dialogy.types.entity.location_entity import LocationEntity

dimension_entity_map = {
    "number": {"value": NumericalEntity},
    "people": {"value": PeopleEntity},
    "time": {"value": TimeEntity, "interval": TimeIntervalEntity},
}

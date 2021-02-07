"""Module provides access to entity types. 

Import functions:

- [entity_synthesis](./base_entity.html)

Import classes:

- [BaseEntity](./base_entity.html)
- [NumericalEntity](./numerical_entity.html)
- [PeopleEntity](./people_entity.html)
- [TimeEntity](./time_entity.html)
- [TimeIntervalEntity](./time_interval_entity.html)
- [LocationEntity](./location_entity.html)
"""

from dialogy.types.entity.base_entity import BaseEntity, entity_synthesis
from dialogy.types.entity.numerical_entity import NumericalEntity
from dialogy.types.entity.people_entity import PeopleEntity
from dialogy.types.entity.time_entity import TimeEntity
from dialogy.types.entity.time_interval_entity import TimeIntervalEntity
from dialogy.types.entity.location_entity import LocationEntity

dimension_entity_map = {
    "number": {"value": NumericalEntity},
    "people": {"value": PeopleEntity},
    "time": {"value": TimeEntity, "interval": TimeIntervalEntity},
}

"""
[tutorial](../../../tests/types/entity/test_entities.html)
"""

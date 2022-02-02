from queue import PriorityQueue

import attr

from dialogy.types import BaseEntity, Intent


@attr.frozen
class Output:
    intents: PriorityQueue[Intent] = attr.ib(validator=attr.validators.instance_of(PriorityQueue))
    entities: PriorityQueue[BaseEntity] = attr.ib(validator=attr.validators.instance_of(PriorityQueue))

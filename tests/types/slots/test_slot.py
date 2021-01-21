from dialogy.types.slots import Slot
from dialogy.types.entities import BaseEntity


def test_slot_build():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
    )
    slot = Slot.fill(entity)
    assert slot.name == entity.slot_name, "Entity slot_name must match."
    assert slot.type == [entity.type], "Slot type should be same as entity type."
    assert (
        slot.values[0] == entity
    ), "Slot value should have 1 item with value same as the entity."


def test_slot_entity_addition():
    body = "12th december"
    entity = BaseEntity(
        range={"from": 0, "to": len(body)},
        body=body,
        dim="default",
        type="basic",
        values=[{"key": "value"}],
    )
    slot = Slot.fill(entity)
    slot.add(entity)
    assert len(slot.values) == 2

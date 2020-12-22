"""
Tests for entities
"""

from dialogy.types.entities import BaseEntity
from dialogy.workflow import Workflow

def mock_plugin(_: Workflow) -> None:
    pass

def test_entity_parser():
    body = "12th december"
    entity = BaseEntity(
        range={
            "from": 0,
            "to": len(body)
        },
        body = body,
        entity_type = "pattern",
        value = body
    )
    entity.add_parser(mock_plugin)

    assert entity.parsers == ["mock_plugin"]

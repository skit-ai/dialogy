"""Module provides Constants to be used throughtout the project.

Import:

- PREPROCESSORS
- POSTPROCESSORS
- WORKFLOW_PUBLIC_PROPERTIES
- BASE_ENTITY_PROPS
- TIME_ENTITY_PROPS
- PEOPLE_ENTITY_PROPS
"""
PREPROCESSORS = "preprocessors"
POSTPROCESSORS = "postprocessors"
DEBUG = "debug"
WORKFLOW_PUBLIC_PROPERTIES = [PREPROCESSORS, POSTPROCESSORS]
S_INTENT_OOS = "_oos_"
TRANSCRIPT = "transcript"
VALUE = "value"
TO = "to"
FROM = "from"


class EntityKeys:
    BODY = "body"
    DIM = "dim"
    END = "end"
    FROM = "from"
    GRAIN = "grain"
    INTERVAL = "interval"
    DURATION = "duration"
    LATENT = "latent"
    RANGE = "range"
    START = "start"
    TO = "to"
    TYPE = "type"
    UNIT = "unit"
    VALUE = "value"
    VALUES = "values"
    ORIGIN = "origin"
    NORMALIZED = "normalized"
    SLOT_NAMES = "slot_names"


SKIP_ENTITY_ATTRS = [
    EntityKeys.DIM,
    EntityKeys.VALUES,
    EntityKeys.LATENT,
    EntityKeys.ORIGIN,
    EntityKeys.SLOT_NAMES,
]

# This section is needed for dialogy.types.entities.*
# Each entity type has a few properties which need to be
# validated for their type.
#
# The actual use-case is, a `dict` is received by the factory
# method of the Entity class, which provides all/enough values to
# instantiate the Entity. We use this mapping to ensure that the
# values belong to expected types.
BASE_ENTITY_PROPS = [
    ([EntityKeys.RANGE], dict),
    ([EntityKeys.RANGE, EntityKeys.START], int),
    ([EntityKeys.RANGE, EntityKeys.END], int),
    ([EntityKeys.BODY], str),
    ([EntityKeys.VALUES], list),
    ([EntityKeys.DIM], str),
    ([EntityKeys.LATENT], bool),
]

TIME_ENTITY_PROPS = BASE_ENTITY_PROPS + [([EntityKeys.GRAIN], str)]
PEOPLE_ENTITY_PROPS = BASE_ENTITY_PROPS + [([EntityKeys.UNIT], str)]

# Time related constants
DATE_UNITS = ["day", "week", "month", "quarter", "year"]
TIME_UNITS = ["hour", "minute", "second"]

# Time Entity types
DATE = "date"
TIME = "time"
DATETIME = "datetime"


# This section covers signals tuple indices
class SIGNAL:
    NAME = 0
    STRENGTH = 1
    REPRESENTATION = 2


KEYWORD = "keyword"
REGEX = "regex"
SPACY = "spacy"

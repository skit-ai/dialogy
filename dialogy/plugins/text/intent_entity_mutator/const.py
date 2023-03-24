BASE_KEY = "swap_rules"
CONDITIONS = "conditions"
MUTATE_TO = "mutate_to"
MUTATE = "mutate"
INTENT = "intent"
ENTITY = "entity"
TRANSCRIPT = "transcript"
STATE = "state"
PREVIOUS_INTENT = "previous_intent"
DIM = "dim"
TYPE = "type"
ENTITY_TYPE = "entity_type"
VALUE = "value"
IN = "in"
NOT_IN = "not_in"
INPUT = "input"
OUTPUT = "output"
MANDATORY_RULE_KEYS = [CONDITIONS, MUTATE, MUTATE_TO]
BASE_ENTITY_PRIMITIVES = [DIM, TYPE, ENTITY_TYPE, VALUE]
SUB_PRIMITIVES = [IN, NOT_IN]
BASE_CONDITION_PRIMITIVES = [
    INTENT,
    ENTITY,
    STATE,
    TRANSCRIPT,
    PREVIOUS_INTENT,
]
ENTITIES = "entities"
ORIGINAL_INTENT = "original_intent"
INTENTS = f"{INTENT}s"
OUTPUT_ATTRIBUTES = {INTENTS, ENTITIES, ORIGINAL_INTENT}
OUTPUT_DEST_INTENT = "output.intents"
OUTPUT_DEST_ENTITY = "output.entities"
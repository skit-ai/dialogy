"""Module provides Constants to be used throughtout the project.

Import:
    - PREPROCESSORS
    - POSTPROCESSORS
    - WORKFLOW_PUBLIC_PROPERTIES
    - BASE_ENTITY_PROPS
    - TIME_ENTITY_PROPS
    - PEOPLE_ENTITY_PROPS
"""
PREPROCESSORS = "__preprocessors"
POSTPROCESSORS = "__postprocessors"
WORKFLOW_PUBLIC_PROPERTIES = [PREPROCESSORS, POSTPROCESSORS]

# ----------------------------------------------------------------
# This section is needed for dialogy.types.entities.*
# Each entity type has a few properties which need to be
# validated for their type.
#
# The actual use-case is, a `dict` is received by the factory
# method of the Entity class, which provides all/enough values to
# instantiate the Entity. We use this mapping to ensure that the
# values belong to expected types.
# ----------------------------------------------------------------
BASE_ENTITY_PROPS = [
    (["range"], dict),
    (["range", "start"], int),
    (["range", "end"], int),
    (["body"], str),
    (["values"], list),
    (["dim"], str),
    (["latent"], bool),
]

TIME_ENTITY_PROPS = BASE_ENTITY_PROPS + [(["grain"], str)]
PEOPLE_ENTITY_PROPS = BASE_ENTITY_PROPS + [(["unit"], str)]
# ----------------------------------------------------------------

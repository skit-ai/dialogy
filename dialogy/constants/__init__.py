"""Module provides Constants to be used throughtout the project.

Import:
    - PREPROCESSORS
    - POSTPROCESSORS
    - WORKFLOW_PUBLIC_PROPERTIES
"""
PREPROCESSORS = "__preprocessors"
POSTPROCESSORS = "__postprocessors"
WORKFLOW_PUBLIC_PROPERTIES = [PREPROCESSORS, POSTPROCESSORS]
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

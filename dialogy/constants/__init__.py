"""Module provides Constants to be used throughtout the project."""

from locale import DAY_1

DEFAULT_NAMESPACE = "vernacular-ai"
DEFAULT_PROJECT_TEMPLATE = "dialogy-template-simple-transformers"

PLUGINS = "plugins"
DEBUG = "debug"
S_INTENT_OOS = "_oos_"
TRANSCRIPT = "transcript"
AM_SCORE = "am_score"
LM_SCORE = "lm_score"
VALUE = "value"
TO = "to"
FROM = "from"
LOCK = "lock"
NAME = "name"
SLOTS = "slots"

DUCKLING_ENTITY_KEYS = ("body", "dim", "end", "latent", "start", "value")
DUCKLING_TIME_VALUES_ENTITY_KEYS = "grain type value values"
DUCKLING_TIME_INTERVAL_ENTITY_KEYS = (
    "from type values",
    "to type values",
    "from to type values",
    "from to",
)

# Time Entity types
DATE = "date"
TIME = "time"
TIME_INTERVAL = "time_interval"
DATETIME = "datetime"
MINUTE = "minute"
HOUR = "hour"
DAY = "day"
MONTH = "month"

PEOPLE = "people"
NUMBER = "number"
AMOUNT_OF_MONEY = "amount-of-money"
DURATION = "duration"
CREDIT_CARD_NUMBER = "credit-card-number"
ADDRESS = "address"
PINCODE = "pincode"

FUTURE = "future"
PAST = "past"
ANY = "__any__"

LTE = "lte"
GTE = "gte"

DUCKLING_DIMS = [PEOPLE, NUMBER, AMOUNT_OF_MONEY, DURATION, CREDIT_CARD_NUMBER, TIME]

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
ENTITY_TYPE = "entity_type"
UNIT = "unit"
VALUE = "value"
VALUES = "values"
ORIGIN = "origin"
ISSUER = "issuer"
NORMALIZED = "normalized"
ALTERNATIVE_INDEX = "alternative_index"
ALTERNATIVE_INDICES = "alternative_indices"
CREDIT_CARD_NUMBER = "credit-card-number"

SLOT_NAMES = "slot_names"
SKIP_ENTITY_ATTRS = [
    DIM,
    VALUES,
    LATENT,
    ORIGIN,
    SLOT_NAMES,
    ALTERNATIVE_INDICES,
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
    ([RANGE], dict),
    ([RANGE, START], int),
    ([RANGE, END], int),
    ([BODY], str),
    ([VALUES], list),
    ([DIM], str),
    ([LATENT], bool),
]

CREDIT_CARD_NUMBER_PROPS = [
    ([RANGE], dict),
    ([RANGE, START], int),
    ([RANGE, END], int),
    ([BODY], str),
    ([VALUE], dict),
    ([DIM], str),
    ([LATENT], bool),
]

TIME_ENTITY_PROPS = BASE_ENTITY_PROPS + [([GRAIN], str)]
PEOPLE_ENTITY_PROPS = BASE_ENTITY_PROPS + [([UNIT], str)]

# Time related constants
DATE_UNITS = ["day", "week", "month", "quarter", "year"]
TIME_UNITS = ["hour", "minute", "second"]


# This section covers signals tuple indices
class SIGNAL:
    NAME = 0
    STRENGTH = 1
    REPRESENTATION = 2


KEYWORD = "keyword"
REGEX = "regex"
SPACY = "spacy"
PWER = "pWER"
ALTERNATIVES = "alternatives"
UTTERANCES = "utterances"

# Transcripts containing less than or equal to this number of for words.
WORD_THRESHOLD = 2

# XLMR
ID = "id"
IDX = "idx"
DATA = "data"
STATE = "state"
LANG = "lang"
NLS_LABEL = "nls_label"
OUTPUT = "output"
INPUT = "input"
CLASSIFICATION_INPUT = "classification_input"
XLMR_MODULE = "simpletransformers.classification"
XLMR_MULTI_CLASS_MODEL = "ClassificationModel"
XLMR_TRAINING_ARGS = "ClassificationArgs"
XLMR_MODEL = "xlmroberta"
XLMR_MODEL_TIER = "xlm-roberta-base"
INTENT = "intent"
ORIGINAL_INTENT = "original_intent"
INTENTS = f"{INTENT}s"
LABELS = "labels"
ENTITIES = "entities"
SCORE = "score"
LABELENCODER_FILE = "labelencoder.pkl"
INVALID_TOKENS = ["<UNK>", "<PAD>", "<SOS>", "<EOS>"]
OUTPUT_ATTRIBUTES = {INTENTS, ENTITIES, ORIGINAL_INTENT}
NULL_PROMPT_TOKEN = "<pad>"

# Training Parameters
EVAL_DATA_DIR = "eval_data_dir"
USE_EARLY_STOPPING = "use_early_stopping"
OVERRIDE_OUTPUT_DIR = "overwrite_output_dir"
TRAIN_BATCH_SIZE = "train_batch_size"
EVAL_BATCH_SIZE = "eval_batch_size"
USE_MULTIPROCESSING = "use_multiprocessing"
USE_MULTIPROCESSING_FOR_EVALUATION = "use_multiprocessing_for_evaluation"
SAVE_MODEL_EVERY_EPOCH = "save_model_every_epoch"
SAVE_BEST_MODEL = "save_best_model"
SAVE_EVAL_CHECKPOINTS = "save_eval_checkpoints"
EARLY_STOPPING_CONSIDER_EPOCHS = "early_stopping_consider_epochs"
EARLY_STOPPING_PATIENCE = "early_stopping_patience"
EARLY_STOPPING_DELTA = "early_stopping_delta"
EARLY_STOPPING_METRIC = "early_stopping_metric"
EARLY_STOPPING_METRIC_MINIMIZE = "early_stopping_metric_minimize"
EVALUATE_DURING_TRAINING = "evaluate_during_training"
EVALUATE_DURING_TRAINING_STEPS = "evaluate_during_training_steps"
EVALUATE_DURING_TRAINING_VERBOSE = "evaluate_during_training_verbose"
EVALUTION_STRATERGY = "evaluation_strategy"
SAVE_STEPS = "save_steps"
FP16 = "fp16"
LEARNING_RATE = "learning_rate"
MAX_SEQ_LENGTH = "max_seq_length"
REPROCESS_INPUT_DATA = "reprocess_input_data"
VALIDATION_SPLIT = "validation_split"

# MLP
MLPMODEL_FILE = "mlpmodelpipeline.joblib"
NUM_TRAIN_EPOCHS = "num_train_epochs"
MLP_DEFAULT_TRAIN_EPOCHS = 25
DEFAULT_NGRAM = (1, 1)
TFIDF_LOWERCASE = False
STOPWORDS = None
MLP_RANDOMSTATE = 1

TFIDF = "tfidf"
MLP = "mlp"

# Hyperparams For MLP
USE_GRIDSEARCH = "gridsearch_hyperparams"
PARAMS = "params"
GRID_SCORETYPE = "weighted"
CV = "cv"
VERBOSE_LEVEL = "verbose_level"
NGRAM_RANGE = "ngram_range"
GRIDSEARCH_WORKERS = -1  # -1 means use all available cores

# Calibration Constants
MODEL_CALIBRATION = "model_calibration"
TS_PARAMETER = "ts_parameter"
CALIBRATION_CONFIG_FILE = "calibration_config.json"
TEMPERATURE = "temperature"

# CLI Commands
TRAIN = "train"
TEST = "test"
PRODUCTION = "production"
CREATE = "create"
UPDATE = "update"
ERROR_LABEL = "_error_"
TEXT = "text"
CANONICALIZED_TRANSCRIPTS = "canonicalized_transcripts"
REFERENCE_TIME = "reftime"
ENTITY_COLUMN = "entities"

FUZZY_DP = "fuzzy_dp"
ENTITY_VALUE_TOKEN = "__value__"

OUTPUT_DIR = "output_dir"
BEST_MODEL_DIR = "best_model_dir"
METRIC_FOR_BEST_MODEL = "metric_for_best_model"
SAVE_TOTAL_LIMIT = "save_total_limit"
BEST_MODEL = BEST_MODEL_DIR
LOCAL_MODEL_DIR = "outputs/best_model"
LOCAL_MODEL_BASE_DIR = "outputs"
MODELS = "models"
METRICS = "metrics"
DATASETS = "datasets"
CLASSIFICATION = "classification"
EPOCHS = "epochs"
PIPELINE_CONFIG_FILE = "pipeline_config.yaml"
CORE_PLUGINS_CONFIG_FILE = "core_plugins_config.yaml"
MODEL_CONFIG_FILE = "model_config.yaml"
TRAINING_PROGRESS_FILE = "training_progress_scores.csv"
LEARNING_CURVE_FILE = "learning_curve.png"
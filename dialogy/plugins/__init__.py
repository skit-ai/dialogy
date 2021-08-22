from dialogy.plugins.postprocess.text.slot_filler.rule_slot_filler import (
    RuleBasedSlotFillerPlugin,
)
from dialogy.plugins.postprocess.text.voting.intent_voting import VotePlugin
from dialogy.plugins.preprocess.text.calibration import (
    WERCalibrationConfig,
    WERCalibrationPlugin,
)
from dialogy.plugins.preprocess.text.duckling_plugin import DucklingPlugin
from dialogy.plugins.preprocess.text.list_entity_plugin import ListEntityPlugin
from dialogy.plugins.preprocess.text.merge_asr_output import MergeASROutputPlugin


from dialogy.plugins.text.calibration.xgb import CalibrationModel
from dialogy.plugins.text.canonicalization import CanonicalizationPlugin
from dialogy.plugins.text.classification.mlp import MLPMultiClass
from dialogy.plugins.text.classification.retain_intent import RetainOriginalIntentPlugin
from dialogy.plugins.text.classification.xlmr import XLMRMultiClass
from dialogy.plugins.text.combine_date_time import CombineDateTimeOverSlots
from dialogy.plugins.text.dob_plugin import DOBPlugin
from dialogy.plugins.text.duckling_plugin import DucklingPlugin
from dialogy.plugins.text.lb_plugin import DucklingPluginLB
from dialogy.plugins.text.list_entity_plugin import ListEntityPlugin
from dialogy.plugins.text.list_search_plugin import ListSearchPlugin
from dialogy.plugins.text.merge_asr_output import MergeASROutputPlugin
from dialogy.plugins.text.slot_filler.rule_slot_filler import RuleBasedSlotFillerPlugin
from dialogy.plugins.text.address_parser import AddressParserPlugin
from dialogy.plugins.text.error_recovery.error_recovery import ErrorRecoveryPlugin
from dialogy.plugins.text.oos_filter import OOSFilterPlugin
from dialogy.plugins.text.intent_entity_mutator import IntentEntityMutatorPlugin
from dialogy.plugins.text.qc_plugin import QCPlugin


plugin_cls_lib = {
    "CalibrationModel": CalibrationModel,
    "CanonicalizationPlugin": CanonicalizationPlugin,
    "MLPMultiClass": MLPMultiClass,
    "MergeASROutputPlugin": MergeASROutputPlugin,
    "DOBPlugin":DOBPlugin,
    "DucklingPlugin": DucklingPlugin,
    "ListEntityPlugin": ListEntityPlugin,
    "XLMRMultiClass": XLMRMultiClass,
    "RuleBasedSlotFillerPlugin": RuleBasedSlotFillerPlugin,
    "AddressParserPlugin": AddressParserPlugin,
    "RetainOriginalIntentPlugin": RetainOriginalIntentPlugin,
    "CombineDateTimeOverSlots": CombineDateTimeOverSlots,
    "DucklingPluginLB": DucklingPluginLB,
    "ListSearchPlugin": ListSearchPlugin,
    "ErrorRecoveryPlugin": ErrorRecoveryPlugin,
    "OOSFilterPlugin": OOSFilterPlugin,
    "IntentEntityMutatorPlugin": IntentEntityMutatorPlugin,
    "QCPlugin": QCPlugin
}
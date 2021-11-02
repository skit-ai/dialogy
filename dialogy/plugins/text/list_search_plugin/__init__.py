"""
.. _list_Search_plugin_

Module needs refactor. We are currently keeping all strategies bundled as methods as opposed to SearchStrategyClasses.

Within dialogy, we extract entities using Duckling, Pattern lists and Spacy. We can ship individual plugins but at the
same time, the difference is just configuration of each of these tools/services. There is another difference of
intermediate structure that the DucklingPlugin expects. We need to prevent the impact of the structure from affecting
all other entities. So that their :code:`from_dict(...)` methods are pristine and involve no shape hacking.
"""
import re
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import stanza
import yaml
from thefuzz import fuzz
from tqdm import tqdm

from dialogy import constants as const
from dialogy.base.entity_extractor import EntityExtractor
from dialogy.base.plugin import PluginFn
from dialogy.types import BaseEntity, KeywordEntity
from dialogy.utils import logger

Text = str
Label = str
Span = Tuple[int, int]
Value = str
Score = float
MatchType = List[Tuple[Text, Label, Value, Span, Score]]  # adding score for each entity


class ListEntityPlugin(EntityExtractor):
    """
     A :ref:`Plugin<plugin>` for extracting entities using spacy or a list of regex patterns.

     .. note: This class will undergo a series of refactoring changes. The final form will accommodate Duckling, Spacy
        and regex based entity parsers.

    :param style: One of ["regex", "spacy"]
    :type style: Optional[str]
    :param candidates: Required if style is "regex", this is a :code:`dict` that shows a mapping of entity
        values and their patterns.
    :type candidates: Optional[Dict[str, List[str]]]
    :param spacy_nlp: Required if style is "spacy", this is a
        `spacy model <https://spacy.io/usage/spacy-101#annotations-ner>`_.
    :type spacy_nlp: Any
    :param labels: Required if style is "spacy". If there is a need to extract only a few labels from all the other
        `available labels <https://github.com/explosion/spaCy/issues/441#issuecomment-311804705>`_.
    :type labels: Optional[List[str]]
    :param access: A plugin io utility that allows access to transcripts
        :code:`List[str]` within a :ref:`Workflow <workflow>`.
    :type access: Optional[PluginFn]
    :param mutate: A plugin io utility that allows insertion of :code:`List[BaseEntity]` within a
        :ref:`Workflow <workflow>`.
    :type mutate: Optional[PluginFn]
    :param debug: A flag to set debugging on the plugin methods
    :type debug: bool
    """

    def __init__(
        self,
        threshold: Optional[float] = None,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = True,
        flags: re.RegexFlag = re.I | re.U,
        debug: bool = False,
        fuzzy_dp_config=None,  # parsed yaml file
        fuzzy_threshold: Optional[float] = 0.1,
        entity_type: str = None, # entity_type passed as an argument

    ):
        super().__init__(
            access=access,
            mutate=mutate,
            debug=debug,
            threshold=threshold,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
        )
        self.__style_search_map = {
            const.FUZZY_DP: self.get_fuzzy_dp_search,
        }

        self.style = (
            const.FUZZY_DP
        )  # which search algo will be used: [regex, spacy, fuzzy]
        self.keywords = None
        self.flags = flags
        """
        Parameters for Fuzzy Dependency Parser defined below
        """

        # ensuring stanza models are downloaded
        stanza.download('en')
        stanza.download('hi')

        self.entity_type = entity_type
        self.fuzzy_dp_config = fuzzy_dp_config[self.entity_type]
        self.entity_dict = {}
        self.entity_patterns = {}
        self.nlp = {}
        self.fuzzy_threshold = fuzzy_threshold

        if self.style == const.FUZZY_DP:
            self.fuzzy_init()

    def fuzzy_init(self):
        """
        Initializing the parameters for fuzzy dp search with their values

        """
        valid_langs = ["hi", "en"]
        for lang_code in self.fuzzy_dp_config.keys():
            if lang_code not in valid_langs:
                raise ValueError(
                    f"Provided language {lang_code} is not supported by this method at present"
                )
            self.entity_dict[lang_code] = self.fuzzy_dp_config[lang_code]
            self.entity_patterns[lang_code] = list(self.entity_dict[lang_code].keys())
            self.nlp[lang_code] = stanza.Pipeline(
                lang=lang_code, tokenize_pretokenized=True
            )

    def _parse(self, candidates: Optional[Dict[str, Dict[str, List[Any]]]]) -> None:
        """
        Pre compile regex patterns to speed up runtime evaluation.

        This method's search will still be slow depending on the list of patterns.

        :param candidates: A map for entity types and their pattern list.
        :type candidates: Optional[Dict[str, List[str]]]
        :return: None
        :rtype: NoneType
        """
        logger.debug(
            pformat(
                {
                    "style": self.style,
                    "candidates": candidates,
                }
            )
        )
        if not isinstance(candidates, dict):
            raise TypeError(
                'Expected "candidates" to be a Dict[str, List[str]]'
                f" but {type(candidates)} was found."
            )

        if not candidates:
            raise ValueError(
                'Expected "candidates" to be a Dict[str, List[str]]'
                f" but {candidates} was found."
            )

        if self.style not in self.__style_search_map:
            raise ValueError(
                f"Expected style to be one of {list(self.__style_search_map.keys())}"
                f' but "{self.style}" was found.'
            )

        logger.debug("compiled patterns")
        logger.debug(self.compiled_patterns)

    def _search(self, transcripts: List[str], lang: str) -> List[MatchType]:
        """
        Search for tokens in a list of strings.

        :param transcripts: A list of transcripts, :code:`List[str]`.
        :type transcripts: List[str]
        :return: Token matches with the transcript.
        :rtype: List[MatchType]
        """
        logger.debug(f"style: {self.style}")
        logger.debug("transcripts")
        logger.debug(transcripts)
        search_fn = self.__style_search_map.get(self.style)
        if not search_fn:
            raise ValueError(
                f"Expected style to be one of {list(self.__style_search_map.keys())}"
                f' but "{self.style}" was found.'
            )
        token_list = [search_fn(transcript, lang=lang) for transcript in transcripts]
        return token_list

    # new method based on experiments done during development of channel parser
    def get_fuzzy_dp_search(self, transcript: str, lang: str = None) -> MatchType:
        """
        Search for Entity in transcript from a defined List Search space
        :param transcripts : A list of transcripts, :code:`List[str]`.
        :param lang : Language code of the transcript :code str
        :return: Token matches with the transcript.
        :rtype: List[MatchType]

        """
        match_dict = {}
        pos_tags = ["PROPN", "NOUN"]
        query = transcript
        # regex variables
        max_length = 0
        final_match = None

        """
        Regex match first
        if we get a match using simple regex we return it 
        """
        for pattern in self.entity_patterns[lang]:
            result = re.search(pattern, query)
            if result:

                match_value = self.entity_dict[lang][result[0]]
                match_length = len(match_value)
                if match_length > max_length:
                    match_text = result[0]
                    max_length = match_length
                    final_match = match_value
                    match_span = result.span()

        # MatchType = List[Tuple[Text, Label, Value, Span]]

        if final_match:
            return [(match_text, self.entity_type, final_match, match_span, float(0))]
        """
        Dependency Parser + Fuzzy Matching 
        if regex fails we use this method 
        """
        sentence = self.nlp[lang](query).sentences[0]
        value = ""
        for word in sentence.words:
            if word.upos in pos_tags:
                if value == "":
                    span_start = word.start_char
                span_end = word.end_char

                """
                joining individual tokens that together are the real entity,
                Since we are dealing with Multi-Word entities here

                """
                value = value + str(word.text) + " "
        if value == "":
            return
        for pattern in self.entity_patterns[lang]:
            val = fuzz.ratio(pattern, value) / 100
            if val > self.fuzzy_threshold:
                match_value = self.entity_dict[lang][pattern]
                match_dict[match_value] = val

        match_output = max(match_dict, key=match_dict.get)
        match_score = match_dict[match_output]

        return [
            (value, self.entity_type, match_output, (span_start, span_end), match_score)
        ]

    def get_entities(self, transcripts: List[str], lang: str) -> List[BaseEntity]:
        """
        Parse entities using regex and spacy ner.

        :param transcripts: A list of strings within which to search for entities.
        :type transcripts: List[str]
        :return: List of entities from regex matches or spacy ner.
        :rtype: List[KeywordEntity]
        """
        matches_on_transcripts = self._search(transcripts, lang)
        logger.debug(matches_on_transcripts)
        entities: List[BaseEntity] = []

        for i, matches_on_transcript in enumerate(matches_on_transcripts):
            for text, label, value, span in matches_on_transcript:
                entity_dict = {
                    "start": span[0],
                    "end": span[1],
                    "body": text,
                    "dim": label,
                    "parsers": [self.__class__.__name__],
                    "score": 0,
                    "alternative_index": i,
                    "latent": False,
                    "__group": f"{label}_{text}",
                    "type": label,
                    "entity_type": label,
                    "value": {
                        "values": [{"value": value}],
                    },
                }

                del entity_dict["__group"]
                entity_ = KeywordEntity.from_dict(entity_dict)
                entity_.add_parser(self).set_value()
                entities.append(entity_)

        logger.debug("Parsed entities")
        logger.debug(entities)

        aggregated_entities = self.entity_consensus(entities, len(transcripts))
        return self.apply_filters(aggregated_entities)

    def utility(self, *args: Any) -> Any:
        return self.get_entities(*args)  # pylint: disable=no-value-for-parameter


    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform training data.

        :param training_data: Training data.
        :type training_data: pd.DataFrame
        :return: Transformed training data.
        :rtype: pd.DataFrame
        """
        if not self.use_transform:
            return training_data

        logger.debug(f"Transforming dataset via {self.__class__.__name__}")
        training_data = training_data.copy()
        if self.output_column not in training_data.columns:
            training_data[self.output_column] = None

        logger.disable("dialogy")
        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            transcripts = self.make_transform_values(row[self.input_column])
            entities = self.utility(transcripts)
            is_empty_series = isinstance(row[self.output_column], pd.Series) and (
                row[self.output_column].isnull()
            )
            is_row_nonetype = row[self.output_column] is None
            is_row_nan = pd.isna(row[self.output_column])
            if is_empty_series or is_row_nonetype or is_row_nan:
                training_data.at[i, self.output_column] = entities
            else:
                training_data.at[i, self.output_column] = (
                    row[self.output_column] + entities
                )
        logger.enable("dialogy")
        return training_data
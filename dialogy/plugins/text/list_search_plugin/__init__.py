"""
.. _list_Search_plugin_

Module needs refactor. We are currently keeping all strategies bundled as methods as opposed to SearchStrategyClasses.

Within dialogy, we extract entities using Duckling, Pattern lists and Spacy. We can ship individual plugins but at the
same time, the difference is just configuration of each of these tools/services. There is another difference of
intermediate structure that the DucklingPlugin expects. We need to prevent the impact of the structure from affecting
all other entities. So that their :code:`from_dict(...)` methods are pristine and involve no shape hacking.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

import stanza
from loguru import logger
from stanza.models.common.doc import Document
from thefuzz import fuzz

from dialogy import constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.base.entity_extractor import EntityScoringMixin
from dialogy.types import BaseEntity, KeywordEntity

Text = str
Label = str
Span = Tuple[int, int]
Value = str
Score = float
MatchType = List[Tuple[Text, Label, Value, Span, Score]]  # adding score for each entity


class ListSearchPlugin(EntityScoringMixin, Plugin):
    """
     A :ref:`Plugin<plugin>` for extracting entities using spacy or a list of regex patterns.

     .. attention:

        This class will undergo a series of refactoring changes. FWIW, :ref:`ListSearchPlugin<ListSearchPlugin>`
        is more more performant in terms of entity capture rates but not as responsive. :code:`ListEntityPlugin`
        is fast. So make choices with bearing this in mind.

    .. _ListSearchPlugin:

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
    :param debug: A flag to set debugging on the plugin methods
    :type debug: bool
    """

    def __init__(
        self,
        fuzzy_dp_config: Dict[Any, Any],  # parsed yaml file
        threshold: Optional[float] = None,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = True,
        flags: re.RegexFlag = re.I | re.U,
        debug: bool = False,
        fuzzy_threshold: Optional[float] = 0.1,
    ):
        super().__init__(
            dest=dest,
            guards=guards,
            debug=debug,
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
        self.threshold = threshold
        """
        Parameters for Fuzzy Dependency Parser defined below
        """

        # ensuring stanza models are downloaded
        stanza.download("en")
        stanza.download("hi")

        self.fuzzy_dp_config = fuzzy_dp_config
        self.entity_dict: Dict[Any, Any] = {}
        self.entity_types: Dict[Any, Any] = {}
        self.nlp: Dict[Any, Any] = {}
        self.fuzzy_threshold = fuzzy_threshold

        if self.style == const.FUZZY_DP:
            self.fuzzy_init()

    def fuzzy_init(self) -> None:
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
            self.entity_types[lang_code] = list(self.entity_dict[lang_code].keys())
            self.nlp[lang_code] = stanza.Pipeline(
                lang=lang_code, tokenize_pretokenized=True
            )

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
        search_fn = self.get_fuzzy_dp_search

        token_list = [search_fn(transcript, lang=lang) for transcript in transcripts]
        return token_list

    def search_regex(
        self,
        query: str,
        entity_type: str = "",
        entity_patterns: Optional[List[str]] = None,
        match_dict: Optional[Dict[Any, Any]] = None,
    ) -> Tuple[Text, Label, Value, Span, Score]:
        match_dict
        max_length = 0
        final_match = None
        entity_patterns = entity_patterns or []
        match_dict = match_dict or {}

        for pattern in entity_patterns:
            result = re.search(pattern, query)
            if result:
                match_value = match_dict[result.group()]
                match_len = len(match_value)
                if match_len > max_length:
                    match_text = result.group()
                    max_length = match_len
                    final_match = match_value
                    match_span = result.span()
        if final_match:
            return (match_text, entity_type, final_match, match_span, 1.0)
        return ("", entity_type, "", (0, 0), 0.0)

    def get_words_from_nlp(
        self, nlp: stanza.Pipeline, query: str
    ) -> List[Dict[str, Any]]:
        document: Document = nlp(query)
        document_json = document.to_dict()
        return document_json[0]

    def dp_search(
        self,
        query: str,
        nlp: stanza.Pipeline,
        entity_type: str = "",
        entity_patterns: Optional[List[str]] = None,
        match_dict: Optional[Dict[Any, Any]] = None,
    ) -> Tuple[Text, Label, Value, Span, Score]:
        entity_patterns = entity_patterns or []
        match_dict = match_dict or {}
        words = self.get_words_from_nlp(nlp, query)
        value = ""
        pos_tags = ["PROPN", "NOUN", "ADP"]
        result_dict = {}
        for word in words:
            if word["upos"] in pos_tags:
                if value == "":
                    span_start = word["start_char"]
                span_end = word["end_char"]

                """
                joining individual tokens that together are the real entity,
                Since we are dealing with Multi-Word entities here
                """
                value = value + str(word["text"]) + " "
        if value != "":
            for pattern in entity_patterns:
                val = fuzz.ratio(pattern, value) / 100
                if val > self.fuzzy_threshold:
                    match_value = match_dict[pattern]
                    result_dict[match_value] = val
            if result_dict:
                match_output = max(result_dict, key=lambda x: result_dict[x])
                match_score = result_dict[match_output]

                return (
                    value,
                    entity_type,
                    match_output,
                    (span_start, span_end),
                    match_score,
                )
        return (value, entity_type, "", (0, 0), 0.0)

    # new method based on experiments done during development of channel parser
    def get_fuzzy_dp_search(self, transcript: str, lang: str = "") -> MatchType:
        """
        Search for Entity in transcript from a defined List Search space
        :param transcripts : A list of transcripts, :code:`List[str]`.
        :param lang : Language code of the transcript :code str
        :return: Token matches with the transcript.
        :rtype: List[MatchType]

        """
        match = []
        query = transcript

        entity_patterns = {}
        entity_match_dict = {}
        for entity_type in self.entity_types[lang]:
            entity_patterns[entity_type] = list(
                self.entity_dict[lang][entity_type].keys()
            )
            entity_match_dict[entity_type] = self.entity_dict[lang][entity_type]
            match_entity = self.search_regex(
                query,
                entity_type,
                entity_patterns[entity_type],
                entity_match_dict[entity_type],
            )

            if match_entity[0] == "":
                match_entity = self.dp_search(
                    query,
                    self.nlp[lang],
                    entity_type,
                    entity_patterns[entity_type],
                    entity_match_dict[entity_type],
                )
            match.append(match_entity)

        return match

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
            for text, label, value, span, score in matches_on_transcript:
                if score == 0.0:
                    continue
                entity_dict = {
                    const.RANGE: {
                        const.START: span[0],
                        const.END: span[1],
                    },
                    const.BODY: text,
                    const.DIM: label,
                    const.SCORE: 0,
                    const.ALTERNATIVE_INDEX: i,
                    const.LATENT: False,
                    "__group": f"{label}_{text}",
                    const.TYPE: label,
                    const.ENTITY_TYPE: label,
                    const.VALUE: value,
                    const.VALUES: [{const.VALUE: value}],
                }

                del entity_dict["__group"]
                entity_ = KeywordEntity.from_dict(entity_dict)
                entity_.add_parser(self)
                entities.append(entity_)

        logger.debug("Parsed entities")
        logger.debug(entities)
        aggregated_entities = self.entity_consensus(entities, len(transcripts))
        return self.apply_filters(aggregated_entities)

    def utility(self, input_: Input, _: Output) -> Any:
        return self.get_entities(
            input_.transcripts, input_.lang
        )  # pylint: disable=no-value-for-parameter

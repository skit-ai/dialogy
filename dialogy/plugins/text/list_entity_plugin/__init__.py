"""
.. _ListEntityPlugin:

Regex Search
-------------

We have often seen certain keywords that gain significance in an SLU project. These keywords are 
easy to extract via patterns and are often used to create entities. The :ref:`ListEntityPlugin<ListEntityPlugin>`
helps in this task, it requires a pattern-map, we call it :code:`candidates`.


.. ipython::

    In [1]: from dialogy.workflow import Workflow
       ...: from dialogy.plugins import ListEntityPlugin
       ...: from dialogy.base import Input

    In [2]: candidates = {
       ...:      "colours": {
       ...:          "red": ["red", "crimson", "ruby", "raspberry"],
       ...:          "blue": ["blue", "azure", "indigo", "navy"],
       ...:          "green": ["green", "emerald", "jade", "teal"],
       ...:      }, 
       ...:    }

    In [2]: list_entity_plugin = ListEntityPlugin(
       ...:   candidates=candidates,
       ...:   style="regex",
       ...:   dest="output.entities"
       ...: )
       ...: workflow = Workflow([list_entity_plugin])
       ...: _, output = workflow.run(Input(utterances="I want an emerald green shirt"))

    In [3]: output

Numeric Values
^^^^^^^^^^^^^^

We can also process numeric entities like so:

.. ipython::

    In [1]: candidates = {
       ...:      "phone-number": {
       ...:          "__value__": ["\d{10}"],
       ...:      }, 
       ...:    }

    In [2]: list_entity_plugin = ListEntityPlugin(
       ...:   candidates=candidates,
       ...:   style="regex",
       ...:   dest="output.entities"
       ...: )
       ...: workflow = Workflow([list_entity_plugin])
       ...: _, output = workflow.run(Input(utterances="my number is 9999999999"))

    In [3]: output


Spacy NER
-----------

We also allow using `spacy's NER <https://spacy.io/usage/spacy-101#annotations-ner>`_. This has to be passed within the
:code:`spacy_nlp` attribute.

.. ipython::

    In [1]: import spacy
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.plugins import ListEntityPlugin
       ...: from dialogy.base import Input

    In [2]: nlp = spacy.load("en_core_web_sm")

    In [3]: list_entity_plugin = ListEntityPlugin(
       ...:   spacy_nlp=nlp,
       ...:   style="spacy",
       ...:   dest="output.entities"
       ...: )
       ...: workflow = Workflow([list_entity_plugin])
       ...: _, output = workflow.run(Input(utterances="Need a place to stay in New Delhi."))

    In [3]: output
"""
import re
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger
from tqdm import tqdm

from dialogy import constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.base.entity_extractor import EntityScoringMixin
from dialogy.types import BaseEntity, KeywordEntity

Text = str
Label = str
Span = Tuple[int, int]
Value = str
MatchType = List[Tuple[Text, Label, Value, Span]]


class ListEntityPlugin(EntityScoringMixin, Plugin):
    """
    A :ref:`Plugin<AbstractPlugin>` for extracting entities using spacy or a list of regex patterns.

    :param style: One of ["regex", "spacy"]
    :type style: Optional[str]
    :param candidates: Required if style is "regex", this is a :code:`dict` that shows a mapping of entity
        values and their patterns.
    :type candidates: Optional[Dict[str, List[str]]]
    :param spacy_nlp: Required if style is "spacy", requires is a
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
        style: Optional[str] = None,
        candidates: Optional[Dict[str, Dict[str, List[Any]]]] = None,
        spacy_nlp: Any = None,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        labels: Optional[List[str]] = None,
        threshold: Optional[float] = None,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = True,
        flags: re.RegexFlag = re.I | re.U,
        debug: bool = False,
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
            const.SPACY: self.ner_search,
            const.REGEX: self.regex_search,
        }

        self.style = style or const.REGEX
        self.labels = labels
        self.threshold = threshold
        self.keywords = None
        self.spacy_nlp = spacy_nlp
        self.compiled_patterns: Dict[str, Dict[str, List[Any]]] = {}
        self.flags = flags

        if self.style == const.REGEX:
            self._parse(candidates)

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
        self.compiled_patterns = {}

        if self.style == const.REGEX:
            for entity_type, entity_value_dict in candidates.items():
                for entity_value, entity_patterns in entity_value_dict.items():
                    patterns = [
                        re.compile(pattern, flags=self.flags)
                        for pattern in entity_patterns
                    ]
                    if not self.compiled_patterns:
                        self.compiled_patterns = {entity_type: {entity_value: patterns}}
                    elif entity_type in self.compiled_patterns:
                        self.compiled_patterns[entity_type][entity_value] = patterns
                    else:
                        self.compiled_patterns[entity_type] = {entity_value: patterns}

        logger.debug("compiled patterns")
        logger.debug(self.compiled_patterns)

    def _search(self, transcripts: List[str]) -> List[MatchType]:
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
        token_list = [search_fn(transcript) for transcript in transcripts]
        return token_list

    def get_entities(self, transcripts: List[str]) -> List[BaseEntity]:
        """
        Parse entities using regex and spacy ner.

        :param transcripts: A list of strings within which to search for entities.
        :type transcripts: List[str]
        :return: List of entities from regex matches or spacy ner.
        :rtype: List[KeywordEntity]
        """
        matches_on_transcripts = self._search(transcripts)
        logger.debug(matches_on_transcripts)
        entities: List[BaseEntity] = []

        for i, matches_on_transcript in enumerate(matches_on_transcripts):
            for text, label, value, span in matches_on_transcript:
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

    def utility(self, input: Input, _: Output) -> Any:
        transcripts = input.transcripts
        return self.get_entities(transcripts)  # pylint: disable=no-value-for-parameter

    def ner_search(self, transcript: str) -> MatchType:
        """
        Wrapper over spacy's ner search.

        :param transcript: A string to search entities within.
        :type transcript: str
        :return: NER parsing via spacy.
        :rtype: MatchType
        """
        if not self.spacy_nlp:
            raise ValueError(
                "Expected spacy_nlp to be a spacy"
                f" instance but {self.spacy_nlp} was found."
            )
        parsed_transcript = self.spacy_nlp(transcript)

        if self.labels:
            return [
                (
                    token.text,
                    token.label_,
                    token.text,
                    (
                        transcript.index(token.text),
                        transcript.index(token.text) + len(token.text),
                    ),
                )
                for token in parsed_transcript.ents
                if token.label_ in self.labels
            ]
        else:
            return [
                (
                    token.text,
                    token.label_,
                    token.text,
                    (
                        transcript.index(token.text),
                        transcript.index(token.text) + len(token.text),
                    ),
                )
                for token in parsed_transcript.ents
            ]

    def regex_search(self, transcript: str) -> MatchType:
        """
        Wrapper over regex searches.

        :param transcript: A string to search entities within.
        :type transcript: str
        :return: regex parsing via spacy.
        :rtype: MatchType
        """
        if not self.compiled_patterns:
            raise TypeError(
                "Expected compiled_patterns to be "
                f"Dict[str, List[str]] but {type(self.compiled_patterns)} was found."
            )

        entity_tokens = []
        for entity_type, entity_value_dict in self.compiled_patterns.items():
            for entity_value, entity_patterns in entity_value_dict.items():
                for pattern in entity_patterns:
                    matches = pattern.search(transcript)
                    if matches:
                        entity_value = (
                            matches.group()
                            if entity_value == const.ENTITY_VALUE_TOKEN
                            else entity_value
                        )
                        entity_tokens.append(
                            (matches.group(), entity_type, entity_value, matches.span())
                        )
        logger.debug(entity_tokens)
        return entity_tokens

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
            entities = self.get_entities(transcripts)
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

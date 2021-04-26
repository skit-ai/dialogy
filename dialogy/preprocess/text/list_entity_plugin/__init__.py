"""
.. _list_entity_plugin:

Module needs refactor. We are currently keeping all strategies bundled as methods as opposed to SearchStrategyClasses.

Within dialogy, we extract entities using Duckling, Pattern lists and Spacy. We can ship individual plugins but at the
same time, the difference is just configuration of each of these tools/services. There is another difference of
intermediate structure that the DucklingPlugin expects. We need to prevent the impact of the structure from affecting
all other entities. So that their :code:`from_dict(...)` methods are pristine and involve no shape hacking.
"""
import re
from pprint import pformat
from typing import Any, Dict, List, Optional, Tuple

import pydash as py_  # type: ignore

from dialogy import constants as const
from dialogy.plugin import Plugin, PluginFn
from dialogy.types import BaseEntity
from dialogy.utils.logger import dbg, log

MatchType = List[Tuple[str, str, Tuple[int, int]]]


class ListEntityPlugin(Plugin):
    """

    :param entity_map: A :code:`dict` with keys as entity type and value as EntityClass
    :type entity_map: Dict[str, BaseEntity]
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
        entity_map: Dict[str, BaseEntity],
        style: Optional[str] = None,
        candidates: Optional[Dict[str, List[str]]] = None,
        spacy_nlp: Any = None,
        labels: Optional[List[str]] = None,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        debug: bool = False,
    ):
        super().__init__(access=access, mutate=mutate, debug=debug)
        self.__style_search_map = {
            const.SPACY: self.ner_search,
            const.REGEX: self.regex_search,
        }

        self.style = style or const.REGEX
        self.entity_map = entity_map
        self.labels = labels
        self.keywords = None
        self.spacy_nlp = spacy_nlp
        self.compiled_patterns: Optional[Dict[str, List[Any]]] = None

        if self.style == const.REGEX:
            self._parse(candidates)

    @dbg
    def _parse(self, candidates: Optional[Dict[str, List[str]]]) -> None:
        log.debug(pformat({
            "style": self.style,
            "candidates": candidates,
        }))
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

        if self.style == const.REGEX:
            self.compiled_patterns = {
                label: [re.compile(pattern) for pattern in patterns]
                for label, patterns in candidates.items()
            }
        log.debug("compiled patterns")
        log.debug(self.compiled_patterns)

    @dbg
    def _search(self, transcripts: List[str]) -> List[MatchType]:
        log.debug("style: %s", self.style)
        log.debug("transcripts")
        log.debug(transcripts)
        search_fn = self.__style_search_map.get(self.style)
        if not search_fn:
            raise ValueError(
                f"Expected style to be one of {list(self.__style_search_map.keys())}"
                f' but "{self.style}" was found.'
            )
        token_list = [search_fn(transcript) for transcript in transcripts]
        return token_list

    @dbg
    def get_entities(self, transcripts: List[str]) -> List[BaseEntity]:
        matches_on_transcripts = self._search(transcripts)
        entity_metadata = []
        entities = []

        for i, matches_on_transcript in enumerate(matches_on_transcripts):
            for text, label, span in matches_on_transcript:
                entity = {
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
                        "values": [{"value": text}],
                    },
                }
                entity_metadata.append(entity)
        entity_groups = py_.group_by(entity_metadata, lambda e: e["__group"])
        log.debug("entity groups:")
        log.debug(pformat(entity_groups))

        for entity_group_name, grouped_entities in entity_groups.items():
            entity = sorted(grouped_entities, key=lambda e: e["alternative_index"])[0]
            del entity["__group"]
            entity["score"] = round(len(grouped_entities) / len(transcripts), 4)
            entity_class = self.entity_map.get(entity["type"]) or BaseEntity  # type: ignore
            entity = entity_class.from_dict(entity).set_value()  # type: ignore
            entities.append(entity)
        log.debug("Parsed entities")
        log.debug(entities)
        return entities  # type:ignore

    def utility(self, *args: Any) -> Any:
        return self.get_entities(*args)

    def ner_search(self, transcript: str) -> MatchType:
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
                    (
                        transcript.index(token.text),
                        transcript.index(token.text) + len(token.text),
                    ),
                )
                for token in parsed_transcript.ents
            ]

    def regex_search(self, transcript: str) -> MatchType:
        if not self.compiled_patterns:
            raise TypeError(
                "Expected compiled_patterns to be "
                f"Dict[str, List[str]] but {type(self.compiled_patterns)} was found."
            )

        entity_tokens = []
        for label, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.search(transcript)
                if matches:
                    entity_tokens.append((matches.group(), label, matches.span()))
        return entity_tokens

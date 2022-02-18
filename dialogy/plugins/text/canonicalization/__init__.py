import copy
import json
import re
import traceback
from typing import Any, Callable, List, Optional

import pandas as pd
from loguru import logger
from tqdm import tqdm

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import BaseEntity
from dialogy.utils import normalize


def get_entity_type(entity: BaseEntity) -> str:
    return f"<{entity.entity_type}>"


class CanonicalizationPlugin(Plugin):
    """
    This plugin implements the canonicalization of the text.
    """

    def __init__(
        self,
        serializer: Callable[[BaseEntity], str] = get_entity_type,
        mask: str = "MASK",
        mask_tokens: Optional[List[str]] = None,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        entity_column: str = const.ENTITY_COLUMN,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        threshold: float = 0.0,
        debug: bool = False,
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            debug=debug,
            use_transform=use_transform,
            input_column=input_column,
            output_column=output_column,
        )
        self.mask = mask
        self.mask_tokens = mask_tokens or []
        self._mask_patterns: List[re.Pattern[str]] = [
            re.compile(r"\b%s\b" % token, re.I | re.U) for token in self.mask_tokens
        ]
        self.serializer = serializer
        self.threshold = threshold
        self.entity_column = entity_column

    def mask_transcript(
        self, entities: List[BaseEntity], transcripts: List[str]
    ) -> List[str]:
        canonicalized_transcripts = copy.copy(transcripts)
        for entity in entities:
            if entity.score is not None and entity.score < self.threshold:
                continue
            if entity.alternative_index is None or not entity.alternative_indices:
                entity  # pylint: disable=pointless-statement
                continue
            start = entity.range[const.START]
            end = entity.range[const.END]
            transcript = transcripts[entity.alternative_index]
            canon = f"{transcript[:start]}{get_entity_type(entity)}{transcript[end:]}"
            for idx in entity.alternative_indices:
                canonicalized_transcripts[idx] = canon

        for i, transcript in enumerate(canonicalized_transcripts):
            for pattern in self._mask_patterns:
                canonicalized_transcripts[i] = pattern.sub(self.mask, transcript)

        return canonicalized_transcripts

    def utility(self, input: Input, output: Output) -> Any:
        entities = output.entities
        transcripts = input.transcripts
        return self.mask_transcript(entities, transcripts)

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        if not self.use_transform:
            return training_data

        logger.debug(f"Transforming dataset via {self.__class__.__name__}")

        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            try:
                canonicalized_transcripts = self.mask_transcript(
                    row[self.entity_column],
                    normalize(json.loads(row[self.input_column])),
                )
                training_data.loc[i, self.output_column] = json.dumps(
                    canonicalized_transcripts
                )
            except Exception as error:  # pylint: disable=broad-except
                logger.error(
                    f"{error} -- {row[self.input_column]}\n{traceback.format_exc()}"
                )
        return training_data

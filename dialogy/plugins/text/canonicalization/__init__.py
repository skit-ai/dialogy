import traceback
from typing import Any, Callable, List, Optional

import pandas as pd  # type: ignore
from tqdm import tqdm  # type: ignore

import dialogy.constants as const
from dialogy.base.plugin import Plugin
from dialogy.types import BaseEntity, plugin
from dialogy.utils import logger


def get_entity_type(entity: BaseEntity) -> str:
    return entity.type


class CanonicalizationPlugin(Plugin):
    """
    This plugin implements the canonicalization of the text.
    """

    def __init__(
        self,
        serializer: Callable[[BaseEntity], str] = get_entity_type,
        mask: str = "MASK",
        mask_tokens: Optional[List[str]] = None,
        access: Optional[plugin.PluginFn] = None,
        mutate: Optional[plugin.PluginFn] = None,
        entity_column: str = const.ENTITY_COLUMN,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        debug: bool = False,
    ) -> None:
        super().__init__(
            access,
            mutate,
            debug=debug,
            use_transform=use_transform,
            input_column=input_column,
            output_column=output_column,
        )
        self.mask = mask
        self.mask_tokens = mask_tokens or []
        self.serializer = serializer
        self.entity_column = entity_column

    def mask_transcript(
        self, entities: List[BaseEntity], transcripts: List[str]
    ) -> List[str]:
        canonicalized_transcripts = []
        for transcript in transcripts:
            for entity in entities:
                transcript = transcript.replace(entity.body, self.serializer(entity))
            for token in self.mask_tokens:
                transcript = transcript.replace(token, self.mask)
            canonicalized_transcripts.append(transcript)
        return canonicalized_transcripts

    def utility(self, *args: Any) -> Any:
        entities, transcripts = args
        return self.mask_transcript(entities, transcripts)

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            try:
                canonicalized_transcripts = self.utility(
                    row[self.entity_column], row[self.input_column]
                )
                training_data.loc[i, self.output_column] = canonicalized_transcripts
            except Exception as error:  # pylint: disable=broad-except
                logger.error(
                    f"{error} -- {row[self.input_column]}\n{traceback.format_exc()}"
                )
        return training_data

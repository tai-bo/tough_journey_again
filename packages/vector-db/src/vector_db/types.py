from typing import Literal

from .enums import VectorNameStrEnum

EmbedActionT = Literal["set", "get"]

SymmetricTaskTypeT = Literal[
  VectorNameStrEnum.CLUSTERING, VectorNameStrEnum.CLASSIFICATION
]

AsymmetricTaskTypeT = Literal[
  VectorNameStrEnum.SEARCH, "question answering", "fact checking"
]

TaskTypeT = AsymmetricTaskTypeT | SymmetricTaskTypeT

CollectionNameT = Literal["moment",]

QueryT = Literal["moment_group", "test"]

PointGroupT = Literal["communities", "isolates"]

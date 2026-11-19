from enum import StrEnum, unique


@unique
class VectorNameStrEnum(StrEnum):
  SEARCH = "search result"
  CLASSIFICATION = "classification"
  CLUSTERING = "clustering"

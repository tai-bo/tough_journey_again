from enum import StrEnum, unique


@unique
class StatusStrEnum(StrEnum):
  INPUT_1000 = "INPUT_1000"  # Saved
  INPUT_1001 = "INPUT_1001"  # Saving
  INPUT_9000 = "INPUT_9000"  # Not Saved


@unique
class ErrorStatusStrEnum(StrEnum):
  INPUT_ERROR_1000 = "INPUT_ERROR_1000"  # No human spoken words.

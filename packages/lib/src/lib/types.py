from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints
from restate.exceptions import TerminalError


def validate_utc_timestamp(value: datetime) -> datetime:
  if value.tzinfo != UTC:
    raise TerminalError(
      message=(f"Expected an UTC datetime, but received: {value}."), status_code=400
    )

  return value


UTCTimestampT = Annotated[datetime, AfterValidator(validate_utc_timestamp)]

StrippedStrT = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

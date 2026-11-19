from typing import Annotated

from pydantic import Field

type AuthUIDT = Annotated[str, Field(min_length=1)]

from typing import Annotated, Literal

from pydantic import Field

type TAIBlobURI = Annotated[str, Field(pattern=r"^gs://tai-")]

AudioContentTypeT = Literal["audio/aac"]

ImageContentTypeT = Literal["image/jpeg", "image/png"]

VideoContentTypeT = Literal["video/quicktime"]

PDFContentTypeT = Literal["application/pdf"]

TextContentTypeT = Literal["text/plain; charset=utf-8"]

InputTypeT = Literal["audio", "image", "video", "text"]

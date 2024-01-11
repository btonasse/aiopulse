from typing import Any, Callable, Coroutine, List

import aiohttp
from pydantic import BaseModel, Field

from .request import Request
from .response import ProcessedResponse
from .schema import InputSchemaBase
from .transformer import TransformerBase

ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], Coroutine[Any, Any, ProcessedResponse]]
Matcher = Callable[[Any], bool]


class RequestBuildMapping(BaseModel):
    """Contains all the needed parts for parsing payloads and building a request

    Attributes:
        title (str): The mapping title
        description(str): The mapping description
        input_schema (InputSchemaBase): The pydantic class representing the expected schema of the raw input. Note this expects the class itself, not an instance
        transformers (list[TransformerBase]): A list of `TransformerBase` types, which will sequentially take the previously validated raw input and further transform it into data ready to construct a `Request`
        response_processor (ResponseProcessor): A function that takes a `aiohttp.ClientResponse` and returns a `ProcessedResponse`
        is_match (Matcher): A predicate function used to check against an input payload if it applies to this mapping
    """

    title: str
    description: str
    input_schema: type[InputSchemaBase]
    transformers: List[type[TransformerBase]] = Field(exclude=True)
    response_processor: ResponseProcessor = Field(exclude=True)
    is_match: Matcher = Field(exclude=True)

    def __str__(self) -> str:
        return f"RequestBuildMapping(title='{self.title}' | input_schema='{self.input_schema.__name__}' | transformers={[t.__name__ for t in self.transformers]} | processor='{self.response_processor.__name__}' | matcher='{self.is_match.__name__}'"

    def get_input_schema(self) -> dict:
        return {"title": self.title, "description": self.description, "input_schema": self.input_schema.model_json_schema()}

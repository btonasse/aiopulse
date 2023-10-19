from typing import Any, TypedDict

from . import Request
from .builder import BuilderBase
from .response import ResponseProcessor
from .schema import InputSchemaBase


class RequestFactoryMapping(TypedDict):
    schema: type[InputSchemaBase]
    builder: BuilderBase
    response_processor: ResponseProcessor


class RequestFactory:
    mappings: list[RequestFactoryMapping]

    def __init__(self) -> None:
        self.mappings = []

    def register_mapping(self, schema: type[InputSchemaBase], builder: BuilderBase, response_processor: ResponseProcessor) -> None:
        self.mappings.append(
            {
                "schema": schema,
                "builder": builder,
                "response_processor": response_processor,
            }
        )

    def build_request(self, data: dict[str, Any]) -> Request:
        for mapping in self.mappings:
            if mapping["schema"].is_match(data):
                input_data = mapping["schema"](**data)
                return mapping["builder"].build_request(input_data, mapping["response_processor"])
        raise ValueError("Data didn't match any registered schemas")

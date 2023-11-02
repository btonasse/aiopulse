from typing import Any, TypedDict

from . import Request
from .response import ResponseProcessor
from .schema import InputSchemaBase
from .transformer import TransformerBase


class RequestFactoryMapping(TypedDict):
    schema: type[InputSchemaBase]
    transformer: TransformerBase
    response_processor: ResponseProcessor


class RequestFactory:
    mappings: list[RequestFactoryMapping]

    def __init__(self) -> None:
        self.mappings = []

    def register_mapping(self, *, schema: type[InputSchemaBase], transformer: TransformerBase, response_processor: ResponseProcessor) -> None:
        self.mappings.append(
            {
                "schema": schema,
                "transformer": transformer,
                "response_processor": response_processor,
            }
        )

    def build_request(self, data: dict[str, Any]) -> Request:
        for mapping in self.mappings:
            if mapping["schema"].is_match(data):
                input_data = mapping["schema"](**data)
                transformed_data = mapping["transformer"].transform_input(input_data.model_dump())
                return Request(response_processor=mapping["response_processor"], **transformed_data)
        raise ValueError("Data didn't match any registered schemas")

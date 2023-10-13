from typing import Any

from . import Request
from .response import ResponseProcessor
from .schema import SchemaBase


class RequestFactory:
    mappings: list[tuple[SchemaBase, ResponseProcessor]]

    def __init__(self) -> None:
        self.mappings = []

    def register_mapping(self, schema: SchemaBase, response_processor: ResponseProcessor) -> None:
        self.mappings.append((schema, response_processor))

    def build_request(self, data: Any) -> Request:
        for mapping in self.mappings:
            if mapping[0].is_match(data):
                return mapping[0].build_request(mapping[1])
        raise ValueError("Data didn't match any registered schemas")

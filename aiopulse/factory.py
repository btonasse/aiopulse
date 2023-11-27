from typing import Any, TypedDict

from .request import Request
from .response import ResponseProcessor
from .schema import InputSchemaBase
from .transformer import TransformerBase


class RequestFactoryMapping(TypedDict):
    schema: type[InputSchemaBase]
    transformers: list[TransformerBase]
    response_processor: ResponseProcessor


class RequestFactory:
    """Create new Request instances based on mappings defined at runtime.

    Attributes:
        `mappings` (list[RequestFactoryMapping]): A list of registered mappings. The order of insertion matters, since they are checked one by one when building a new `Request`

    Methods:
        `register_mapping`: register new mappings.
        `build_request`: check if data matches any of the registered mappings and return a new Request
    """

    mappings: list[RequestFactoryMapping]

    def __init__(self) -> None:
        self.mappings = []

    def register_mapping(self, *, schema: type[InputSchemaBase], transformers: list[TransformerBase], response_processor: ResponseProcessor) -> None:
        """Register a new schema+transformer+response_processor mapping.

        Args:
            schema (type[InputSchemaBase]): The pydantic class representing the expected schema of the raw input. Note this expects the class itself, not an instance
            transformers (list[TransformerBase]): A list of `TransformerBase` instances, which will sequentially take the previously validated raw input and further transform it into data ready to construct a `Request`
            response_processor (ResponseProcessor): A function that takes a `aiohttp.ClientResponse` and returns a `ProcessedResponse`
        """
        self.mappings.append(
            {
                "schema": schema,
                "transformers": transformers,
                "response_processor": response_processor,
            }
        )

    def build_request(self, data: dict[str, Any]) -> Request:
        """Checks if the input data matches any previously registered mappings and build a new `Request` after being validated/transformed.

        Note that the order of mapping registration is important, since they are checked one by one in insertion order until a match is found

        Args:
            data (dict[str, Any]): A dictionary with the raw input data

        Raises:
            ValueError: If the data doesn't match any of the mappings or the expected values in the transformer method
            pydantic.ValidationError: If the input data doesn't match the schema or the transformer's

        Returns:
            A new `Request` instance
        """
        for mapping in self.mappings:
            if mapping["schema"].is_match(data):
                input_data = mapping["schema"](**data)
                transformed_data = self.apply_transforms(input_data.model_dump(exclude={"chain"}), mapping["transformers"])
                return Request(response_processor=mapping["response_processor"], **transformed_data)
        raise ValueError("Data didn't match any registered schemas")

    def apply_transforms(self, data: dict[str, Any], transformers: list[TransformerBase]) -> dict[str, Any]:
        """Apply each transformer in the order of insertion.

        Args:
            data (dict[str, Any]): Data to be transformed
            transformers (list[TransformerBase]): List of transformers to be applied

        Returns:
            dict[str, Any]: A new dictionary with the transformed data
        """
        copied_data = dict(data)
        for transformer in transformers:
            copied_data = transformer.transform_input(copied_data)
        return copied_data

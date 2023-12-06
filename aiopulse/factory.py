import logging
from typing import Any, Callable, Coroutine, TypedDict

import aiohttp
from pydantic import ValidationError

from .request import Request
from .response import ProcessedResponse
from .schema import InputSchemaBase
from .transformer import TransformerBase

ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], Coroutine[Any, Any, ProcessedResponse]]


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
        self.logger = logging.getLogger(__name__)
        self.mappings = []
        self.logger.debug("RequestFactory initialized.")

    def register_mapping(self, *, schema: type[InputSchemaBase], transformers: list[TransformerBase], response_processor: ResponseProcessor) -> None:
        """Register a new schema+transformer+response_processor mapping.

        Args:
            schema (type[InputSchemaBase]): The pydantic class representing the expected schema of the raw input. Note this expects the class itself, not an instance
            transformers (list[TransformerBase]): A list of `TransformerBase` instances, which will sequentially take the previously validated raw input and further transform it into data ready to construct a `Request`
            response_processor (ResponseProcessor): A function that takes a `aiohttp.ClientResponse` and returns a `ProcessedResponse`
        """
        self.logger.info(f"New request mapping: schema '{schema.__name__}' | transformers: {[t.__class__.__name__ for t in transformers]} | processor: '{response_processor.__name__}'")
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
        self.logger.info("Building request...")
        try:
            for mapping in self.mappings:
                schema = mapping["schema"]
                if schema.is_match(data):
                    self.logger.info(f"Schema '{schema.__name__}' matched request data")
                    input_data = schema(**data)
                    transformed_data = self.apply_transforms(input_data.model_dump(exclude={"chain"}), mapping["transformers"])
                    return Request(response_processor=mapping["response_processor"], **transformed_data)
        except (ValidationError, ValueError) as err:
            self.logger.error(f"Failed building request. Error: {str(err)}")
            raise
        self.logger.warning("Data didn't match any registered schemas")
        raise ValueError("Data didn't match any registered schemas")

    def apply_transforms(self, data: dict[str, Any], transformers: list[TransformerBase]) -> dict[str, Any]:
        """Apply each transformer in the order of insertion.

        Args:
            data (dict[str, Any]): Data to be transformed
            transformers (list[TransformerBase]): List of transformers to be applied

        Returns:
            dict[str, Any]: A new dictionary with the transformed data
        """
        self.logger.info(f"Applying {len(transformers)} transformers to input data...")
        copied_data = dict(data)
        for transformer in transformers:
            self.logger.info(f"Applying '{transformer.__class__.__name__}'...")
            copied_data = transformer.transform_input(copied_data)
        return copied_data

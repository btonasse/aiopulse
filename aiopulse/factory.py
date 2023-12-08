import logging
from typing import Any, Callable, Coroutine

import aiohttp
from pydantic import BaseModel

from .request import Request
from .response import ProcessedResponse
from .schema import InputSchemaBase
from .transformer import TransformerBase

ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], Coroutine[Any, Any, ProcessedResponse]]
Matcher = Callable[[Any], bool]


class RequestFactoryMapping(BaseModel):
    """Contains all the needed parts for parsing payloads and building a request

    Attributes:
        input_schema (type[InputSchemaBase]): The pydantic class representing the expected schema of the raw input. Note this expects the class itself, not an instance
        transformers (list[type[TransformerBase]]): A list of `TransformerBase` types, which will sequentially take the previously validated raw input and further transform it into data ready to construct a `Request`
        response_processor (ResponseProcessor): A function that takes a `aiohttp.ClientResponse` and returns a `ProcessedResponse`
        is_match (Matcher): A predicate function used to check against an input payload if it applies to this mapping
    """

    input_schema: type[InputSchemaBase]
    transformers: list[type[TransformerBase]]
    response_processor: ResponseProcessor
    is_match: Matcher

    def __str__(self) -> str:
        return f"RequestFactoryMapping(input_schema='{self.input_schema.__name__}' | transformers={[t.__name__ for t in self.transformers]} | processor='{self.response_processor.__name__}' | matcher='{self.is_match.__name__}'"


class RequestFactory:
    """Create new Request instances based on mappings defined at runtime.

    Args:
        `transformer_args`: A dictionary containing arguments to be passed to the transformer constructors

    Attributes:
        `mappings` (list[RequestFactoryMapping]): A list of registered mappings. The order of insertion matters, since they are checked one by one when building a new `Request`

    Methods:
        `register_mapping`: register new mappings.
        `build_request`: check if data matches any of the registered mappings and return a new Request
    """

    mappings: list[RequestFactoryMapping]

    def __init__(self, **transformer_args) -> None:
        self.logger = logging.getLogger(__name__)
        self.mappings = []
        self.transformer_args = transformer_args or dict()
        self.logger.debug("RequestFactory initialized.")

    def register_mapping(self, mapping: RequestFactoryMapping) -> None:
        """Register a new  mapping.

        Args:
            mapping (RequestFactoryMapping): An object containing schema+transformer+response_processor+matcher - all the parts needed to build a new request
        """
        self.logger.info(f"New request mapping: {mapping}")
        self.mappings.append(mapping)

    def build_request(self, data: dict[str, Any]) -> Request:
        """Checks if the input data matches any previously registered mappings and build a new `Request` after being validated/transformed.

        Note that the order of mapping registration is important, since they are checked one by one in insertion order until a match is found

        Args:
            data (dict[str, Any]): A dictionary with the raw input data

        Raises:
            ValueError: If the data doesn't match any of the mappings, the input data doesn't pass validation or the transformation fails.
            In fact, all error types are reraised as ValueError.

        Returns:
            A new `Request` instance
        """
        self.logger.info("Building request...")
        try:
            for mapping in self.mappings:
                if mapping.is_match(data):
                    self.logger.info(f"Mapping {mapping} matched request data")
                    input_data = mapping.input_schema(**data)
                    transformed_data = self.apply_transforms(input_data.model_dump(exclude={"chain"}), mapping.transformers)
                    request = Request(response_processor=mapping.response_processor, **transformed_data)
                    self.logger.info("New request (id %s) successfully created", request.id)
                    return request
        except Exception as err:
            self.logger.error(f"Failed building request. {err.__class__.__name__}: {err}")
            raise ValueError("Failed building request.") from err
        self.logger.warning("Data didn't match any registered schemas")
        raise ValueError("Data didn't match any registered schemas")

    def apply_transforms(self, data: dict[str, Any], transformers: list[type[TransformerBase]]) -> dict[str, Any]:
        """Apply each transformer in the order of insertion.

        Args:
            data (dict[str, Any]): Data to be transformed
            transformers (list[type[TransformerBase]]): List of transformers to be applied

        Returns:
            dict[str, Any]: A new dictionary with the transformed data
        """
        self.logger.info(f"Applying {len(transformers)} transformers to input data...")
        copied_data = dict(data)
        for transformer in transformers:
            transformer_instance = transformer(**self.transformer_args)
            self.logger.info(f"Applying '{transformer.__name__}'...")
            copied_data = transformer_instance.transform_input(copied_data)
        return copied_data

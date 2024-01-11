import logging
from typing import Any

from .mapping import RequestBuildMapping
from .request import Request
from .transformer import TransformerBase


class RequestFactory:
    """Create new Request instances based on mappings defined at runtime.

    Attributes:
        `mappings` (list[RequestFactoryMapping]): A list of registered mappings. The order of insertion matters, since they are checked one by one when building a new `Request`
        `transformer_args`: A dictionary containing arguments to be passed to the transformer constructors

    Methods:
        `register_mapping`: register new mappings.
        `build_request`: check if data matches any of the registered mappings and return a new Request
    """

    mappings: list[RequestBuildMapping]

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.mappings = []
        self.transformer_args = dict()
        self.logger.debug("RequestFactory initialized.")

    def register_mapping(self, mapping: RequestBuildMapping) -> None:
        """Register a new  mapping.

        Args:
            mapping (RequestBuildMapping): An object containing schema+transformer+response_processor+matcher - all the parts needed to build a new request
        """
        self.logger.info(f"New request mapping: {mapping}")
        self.mappings.append(mapping)

    def build_request(self, data: dict[str, Any], extra_input_args: dict[str, Any] = dict()) -> Request:
        """Checks if the input data matches any previously registered mappings and builds a new `Request` after being validated/transformed.

        Note that the order of mapping registration is important, as they are checked one by one in insertion order until a match is found.

        Args:
            data (dict[str, Any]): A dictionary with the raw input data.
            extra_input_args (dict[str, Any], optional): Additional input arguments to be passed to the input schema. Defaults to an empty dictionary.

        Raises:
            ValueError: If the data doesn't match any of the mappings, the input data doesn't pass validation, or the transformation fails.

        Returns:
            Request: A new `Request` instance.
        """
        self.logger.info("Building request...")
        try:
            for mapping in self.mappings:
                if mapping.is_match(data):
                    self.logger.info(f"Mapping {mapping} matched request data")
                    input_data = mapping.input_schema(**data | extra_input_args)
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

    def set_transformer_args(self, **transformer_args) -> None:
        self.transformer_args = transformer_args

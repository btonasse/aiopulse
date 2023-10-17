import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from yarl import URL

from .request import Request
from .response import ResponseProcessor
from .schema import InputSchemaBase


class BuilderBase(BaseModel, abc.ABC):
    @abc.abstractmethod
    def build_request(self, input_data: InputSchemaBase, response_processor: ResponseProcessor) -> Request:
        raise NotImplementedError


class GenericBuilder(BuilderBase):
    def build_request(self, input_data: InputSchemaBase, response_processor: ResponseProcessor) -> Request:
        return Request(response_processor=response_processor, **input_data.model_dump())


class BaseURLBuilder(BuilderBase):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    base_url: URL

    # Todo: I'm repeating myself with this validation
    @field_validator("base_url", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> URL:
        try:
            url = URL(v)
        except TypeError as err:
            raise ValueError("Cannot construct URL from a type other than str")
        if not url.is_absolute():
            raise ValueError("Could not construct an absolute URL")
        return url

    def build_request(self, input_data: InputSchemaBase, response_processor: ResponseProcessor) -> Request:
        # Make sure input data can be combined with base url
        if input_data.url.is_absolute():
            raise ValueError("Expected input url to be relative but got absolute. Cannot combine with base url.")
        # Combine base_url with input URL
        query = input_data.url.query  # yarl for some reason doesn't allow for joining a path without destroying query params. We need to prevent this here.
        joined_url = self.base_url.join(input_data.url)
        with_query = joined_url.with_query(query)
        return Request(response_processor=response_processor, url=with_query, **input_data.model_dump(exclude={"url"}))

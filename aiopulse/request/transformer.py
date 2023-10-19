import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from yarl import URL


class TransformerBase(BaseModel, abc.ABC):
    @abc.abstractmethod
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class GenericTransformer(TransformerBase):
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return input_data


class BaseURLTransformer(TransformerBase):
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
        if url.query_string:
            raise ValueError("Unexpected query parameters in base url")
        return url

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        url: URL | None = input_data.get("url")
        if not url or not isinstance(url, URL):
            raise ValueError("Input data does not have a url attribute or it is not a URL instance.")
        # Make sure input data can be combined with base url
        if url.is_absolute():
            raise ValueError("Expected input url to be relative but got absolute. Cannot combine with base url.")
        # Combine base_url with input URL
        joined_url = self.base_url.joinpath(str(url), encoded=True)  # type: ignore - necessary because for some reason the linter thinks the "encoded" parameter is not part of this method's signature.
        copied_data = dict(input_data)
        copied_data["url"] = joined_url
        return copied_data

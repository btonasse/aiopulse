import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from yarl import URL


class TransformerBase(BaseModel, abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abc.abstractmethod
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class AddBaseURL(TransformerBase):
    base_url: URL

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
        url: URL = input_data["url"]
        if not url:
            input_data["url"] = self.base_url
        else:
            if not isinstance(url, URL):
                raise ValueError("Input url needs to be a URL instance")
            if url.is_absolute():
                raise ValueError("Expected input url to be relative but got absolute. Cannot combine with base url.")
            input_data["url"] = self.base_url.joinpath(str(url), encoded=True)  # type: ignore - necessary because for some reason the linter thinks the "encoded" parameter is not part of this method's signature.
        return input_data


class AddPathToURL(TransformerBase):
    path_to_add: URL

    @field_validator("path_to_add", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> URL:
        try:
            url = URL(v)
        except TypeError as err:
            raise ValueError("Cannot construct URL from a type other than str")
        if url.is_absolute():
            raise ValueError("URL cannot be absolute")
        return url

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        url: URL = input_data["url"]
        qstring = url.query_string
        input_data["url"] = url.with_path(url.path + self.path_to_add.path) % qstring
        return input_data

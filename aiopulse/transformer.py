import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from .data_types import SerializableURL


class TransformerBase(BaseModel, abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abc.abstractmethod
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class AddBaseURL(TransformerBase):
    base_url: SerializableURL

    @field_validator("base_url", mode="after")
    @classmethod
    def validate_url(cls, v: SerializableURL) -> SerializableURL:
        if not v.is_absolute():
            raise ValueError("Could not construct an absolute URL")
        if v.query_string:
            raise ValueError("Unexpected query parameters in base url")
        return v

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        url: SerializableURL | None = input_data.get("url")
        if not url:
            input_data["url"] = self.base_url
        else:
            if not isinstance(url, SerializableURL):
                raise ValueError("Input url needs to be a URL instance")
            if url.is_absolute():
                raise ValueError("Expected input url to be relative but got absolute. Cannot combine with base url.")
            input_data["url"] = self.base_url.joinpath(str(url), encoded=True)  # type: ignore - necessary because for some reason the linter thinks the "encoded" parameter is not part of this method's signature.
        return input_data


class AddPathToURL(TransformerBase):
    path_to_add: SerializableURL

    @field_validator("path_to_add", mode="after")
    @classmethod
    def validate_url(cls, v: SerializableURL) -> SerializableURL:
        if v.is_absolute():
            raise ValueError("URL cannot be absolute")
        return v

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        url: SerializableURL = input_data["url"]
        qstring = url.query_string
        input_data["url"] = url.with_path(url.path + self.path_to_add.path) % qstring
        return input_data

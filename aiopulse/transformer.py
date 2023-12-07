import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from yarl import URL

from aiopulse.request import Method


class TransformerBase(BaseModel, abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @abc.abstractmethod
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class GenericTransformer(TransformerBase):
    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        return input_data


class BaseURLTransformer(TransformerBase):
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


class AddMethod(TransformerBase):
    method: Method

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        copied_data["method"] = self.method
        return copied_data


class AddHeaders(TransformerBase):
    headers: dict[str, str]

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        copied_data["headers"] = input_data["headers"] | self.headers
        return copied_data


class AddQueryParams(TransformerBase):
    params: dict[str, str]

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        copied_data["query_params"] = input_data["query_params"] | self.params
        return copied_data


class AddFormData(TransformerBase):
    form_data: dict[str, Any]

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        copied_data["form_data"] = input_data["form_data"] | self.form_data
        return copied_data


class AddToBody(TransformerBase):
    body: dict[str, Any]

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        copied_data["body"] = input_data["body"] | self.body
        return copied_data


class AddPathToURL(TransformerBase):
    path: URL

    def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        copied_data = dict(input_data)
        url: URL = input_data["url"]
        qstring = url.query_string
        copied_data["url"] = url.with_path(url.path + self.path.path) % qstring
        return copied_data

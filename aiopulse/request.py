from __future__ import annotations

from enum import StrEnum, auto
from typing import Any, Callable

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from yarl import URL

from .response import ProcessedResponse, ResponseProcessor


class Counter:
    _counter: int = 0

    def __call__(self) -> int:
        Counter._counter += 1
        return Counter._counter


class Method(StrEnum):
    """
    HTTP methods enum
    """

    GET = auto()
    POST = auto()
    PUT = auto()
    PATCH = auto()
    DELETE = auto()

    @classmethod
    def _missing_(cls, value: str):
        # Accept values in all cases
        for member in cls:
            if member.lower() == value.lower():
                return member


class Request(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int = Field(default_factory=Counter())
    description: str
    url: URL
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)
    response_processor: ResponseProcessor = Field(exclude=True)

    @model_validator(mode="before")
    @classmethod
    def no_id_in_payload(cls, data: Any) -> Any:
        try:
            if data.get("id"):
                raise ValueError("'id' is a reserved keyword and cannot be used in the request construction payload")
        except AttributeError as err:
            raise ValueError(str(err))
        return data

    @model_validator(mode="before")
    @classmethod
    def validate_response_processor(cls, data: Any) -> Any:
        try:
            processor = data.get("response_processor")
            assert processor is not None and isinstance(processor, Callable), "No response processor"
        except AttributeError as err:
            raise ValueError(str(err))
        return data

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> URL:
        try:
            url = URL(v)
        except TypeError as err:
            raise ValueError("Cannot construct URL from a type other than str")
        if not url.is_absolute():
            raise ValueError("Could not construct an absolute URL")
        return url

    @model_validator(mode="after")
    def either_payload_or_formdata(self) -> Request:
        if self.body and self.form_data:
            raise ValueError("Request cannot have both a body and form data")
        return self

    @model_validator(mode="after")
    def add_query_params(self) -> Request:
        self.url = self.url.with_query(self.query_params)
        return self

    async def process_response(self, response: aiohttp.ClientResponse) -> ProcessedResponse:
        resp = await self.response_processor(response)
        return resp

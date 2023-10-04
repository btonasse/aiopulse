from __future__ import annotations

from enum import StrEnum, auto
from typing import Any, Awaitable, Callable

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from yarl import URL


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


class RequestParams(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    url: URL
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)

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
    def either_payload_or_formdata(self) -> RequestParams:
        if self.body and self.form_data:
            raise ValueError("Request cannot have both a body and form data")
        return self

    @model_validator(mode="after")
    def add_query_params(self) -> RequestParams:
        self.url = self.url.with_query(self.query_params)
        return self


class ProcessedResponse(BaseModel):
    ok: bool
    status: int = Field(ge=100, lt=600)
    content: list[dict[str, Any]] | None
    error: str | None
    request: Request
    next_request: Request | None = None


ResponseProcessor = Callable[[aiohttp.ClientResponse], Awaitable[ProcessedResponse]]

ParamsBuilder = Callable[[dict[str, Any]], RequestParams]


class Request:
    _params: RequestParams
    _processor: ResponseProcessor

    def __init__(
        self,
        raw_params: dict[str, Any],
        params_builder: ParamsBuilder,
        response_processor: ResponseProcessor,
    ) -> None:
        self._params = params_builder(raw_params)
        self._processor = response_processor

    @property
    def url(self) -> str:
        return str(self._params.url)

    @property
    def method(self) -> str:
        return self._params.method.name

    @property
    def body(self) -> dict[str, Any]:
        return self._params.body

    @property
    def headers(self) -> dict[str, str]:
        return self._params.headers

    @property
    def form_data(self) -> dict[str, Any]:
        return self._params.form_data

    @property
    def query_params(self) -> dict[str, str]:
        return self._params.query_params

    async def process_response(self, response: aiohttp.ClientResponse) -> Awaitable[ProcessedResponse]:
        return self._processor(response)

from __future__ import annotations

from typing import Any, Callable, Coroutine

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .data_types import Counter, Method, SerializableURL
from .response import ProcessedResponse


class Request(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: int = Field(default_factory=Counter())
    description: str
    url: SerializableURL
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict, exclude=True)
    response_processor: Callable[[aiohttp.ClientResponse, Request], Coroutine[Any, Any, ProcessedResponse]] = Field(exclude=True)

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

    @field_validator("url", mode="after")
    @classmethod
    def validate_url(cls, v: SerializableURL) -> SerializableURL:
        if not v.is_absolute():
            raise ValueError("Could not construct an absolute URL")
        return v

    @model_validator(mode="after")
    def either_payload_or_formdata(self) -> Request:
        if self.body and self.form_data:
            raise ValueError("Request cannot have both a body and form data")
        return self

    @model_validator(mode="after")
    def add_query_params(self) -> Request:
        self.url = self.url.update_query(self.query_params)  # type: ignore
        return self

    def prepare(self) -> dict[str, Any]:
        """
        Prepares the request parameters for aiohttp's request method.

        Returns:
            dict[str, Any]: The prepared request parameters.
        """
        params = {
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
        }
        if self.body:
            params["json"] = self.body
        elif self.form_data:
            params["data"] = self.form_data
        return params

    async def process_response(self, response: aiohttp.ClientResponse) -> ProcessedResponse:
        resp = await self.response_processor(response, self)
        return resp

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from yarl import URL

from .request import Method


class InputSchemaBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    chain: list[InputSchemaBase] | None = None


class GenericInputSchema(InputSchemaBase):
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
        return url

from __future__ import annotations

import abc
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from yarl import URL

from .request import Method


class InputSchemaBase(BaseModel, abc.ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    url: URL
    chain: list[InputSchemaBase] | None = None

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(cls, v: Any) -> URL:
        try:
            url = URL(v)
        except TypeError as err:
            raise ValueError("Cannot construct URL from a type other than str")
        return url

    @classmethod
    @abc.abstractmethod
    def is_match(cls, data: Any) -> bool:
        raise NotImplementedError


class GenericInputSchema(InputSchemaBase):
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def is_match(cls, data: Any) -> bool:
        # No validation at all. This is the fallback schema.
        return True
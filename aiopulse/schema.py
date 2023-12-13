from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .data_types import Method, SerializableURL


class InputSchemaBase(BaseModel):
    # model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    chain: list[dict[str, Any]] | None = None

    class Config:
        arbitrary_types_allowed = True

        @staticmethod
        def json_schema_extra(schema: dict[str, Any], model: type["InputSchemaBase"]) -> None:
            for prop in schema.get("properties", {}).values():
                prop.pop("title", None)


class GenericInputSchema(InputSchemaBase):
    """Generic schema, ready to be passed as-is to the Request constructor"""

    url: SerializableURL
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)

from __future__ import annotations

from typing import Any, Type

from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from yarl import URL

from .request import Method

del URL.__init_subclass__


class SerializableUrl(URL):  # type: ignore
    @classmethod
    def __get_pydantic_core_schema__(cls, source: Type[Any], handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        assert source is SerializableUrl
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                cls._serialize,
                info_arg=False,
                return_schema=core_schema.str_schema(),
            ),
        )

    @staticmethod
    def _validate(value: str) -> "SerializableUrl":
        try:
            return SerializableUrl(value)
        except TypeError as err:
            raise ValueError("Cannot construct URL from a type other than str") from err

    @staticmethod
    def _serialize(value: "SerializableUrl") -> str:
        return str(value)


class InputSchemaBase(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    description: str
    chain: list[dict[str, Any]] | None = None


class GenericInputSchema(InputSchemaBase):
    """Generic schema, ready to be passed as-is to the Request constructor"""

    url: SerializableUrl
    method: Method
    body: dict[str, Any] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    form_data: dict[str, Any] = Field(default_factory=dict)
    query_params: dict[str, str] = Field(default_factory=dict)

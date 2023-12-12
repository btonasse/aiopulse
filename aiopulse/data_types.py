from enum import StrEnum, auto
from typing import Any

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from yarl import URL

# Allow subclassing yarl.URL
del URL.__init_subclass__


class SerializableURL(URL):  # type: ignore
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        def _validate(value: str | URL | SerializableURL) -> SerializableURL:
            try:
                return SerializableURL(value)
            except TypeError as err:
                raise ValueError("Cannot construct URL from a type other than str") from err

        return core_schema.no_info_plain_validator_function(
            function=_validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, _core_schema: CoreSchema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        return handler(core_schema.str_schema())


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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from custom_types import Method
from yarl import URL


@dataclass
class RequestParams:
    url: URL
    method: Method
    payload: dict[str, Any] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    form_data: dict[str, Any] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.payload and self.form_data:
            raise TypeError("Request cannot have both a body and form data")


class RequestParamsBuilder(ABC):
    @classmethod
    @abstractmethod
    def parse_params(cls, data: dict[str, Any]) -> RequestParams:
        pass

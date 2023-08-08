from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import aiohttp

from ..query import Query


@dataclass
class ProcessedResponse:
    ok: bool
    status: int
    content: dict[str, Any]
    error: str | None
    query: Query
    next_query: Query | None = None


class ResponseProcessor(ABC):
    @classmethod
    @abstractmethod
    def process_response(cls, response: aiohttp.ClientResponse) -> ProcessedResponse:
        pass

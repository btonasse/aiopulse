from typing import Any, Awaitable, Callable

import aiohttp
from pydantic import BaseModel, Field

from . import Request


class ProcessedResponse(BaseModel):
    ok: bool
    status: int = Field(ge=100, lt=600)
    content: list[dict[str, Any]] | None
    error: str | None
    request: Request
    next_request: Request | None = None


ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], Awaitable[ProcessedResponse]]


async def simple_processor(response: aiohttp.ClientResponse) -> Awaitable[ProcessedResponse]:
    raise NotImplementedError

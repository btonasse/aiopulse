from typing import Any, Callable, Coroutine

import aiohttp
from pydantic import BaseModel, Field

from .request import Request


class ProcessedResponse(BaseModel):
    status: int = Field(ge=100, lt=600)
    content: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None
    request: Request
    chain: list[dict[str, Any]] = Field(default_factory=list)


ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], Coroutine[Any, Any, ProcessedResponse]]


async def simple_json_processor(response: aiohttp.ClientResponse, request: Request) -> ProcessedResponse:
    if response.status >= 400:
        content = []
        error = response.reason
    else:
        resp_json: dict[str, Any] | list[dict[str, Any]] = await response.json()
        error = None
        if isinstance(resp_json, dict):
            content = [resp_json]
        else:
            content = resp_json

    return ProcessedResponse(status=response.status, content=content, error=error, request=request)

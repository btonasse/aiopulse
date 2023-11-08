from typing import Any, Callable

import aiohttp
from pydantic import BaseModel, Field

from .request import Request


class ProcessedResponse(BaseModel):
    ok: bool
    status: int = Field(ge=100, lt=600)
    content: list[dict[str, Any]] | None
    error: str | None
    request: Request
    chain: list[Request] = Field(default_factory=list)


ResponseProcessor = Callable[[aiohttp.ClientResponse, Request], ProcessedResponse]


async def simple_json_processor(response: aiohttp.ClientResponse, request: Request) -> ProcessedResponse:
    if response.status >= 400:
        content = None
        error = response.reason
    else:
        resp_json: dict[str, Any] | list[dict[str, Any]] = await response.json()
        error = None
        if isinstance(resp_json, dict):
            content = [resp_json]
        else:
            content = resp_json

    return ProcessedResponse(ok=response.ok, status=response.status, content=content, error=error, request=request)

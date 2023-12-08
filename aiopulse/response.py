from typing import Any

import aiohttp
from pydantic import BaseModel, Field


class ProcessedResponse(BaseModel):
    ok: bool
    status: int = Field(ge=100, lt=600)
    content: list[dict[str, Any]] = Field(default_factory=list)
    error: str | None = None
    chain: list[dict[str, Any]] = Field(default_factory=list)
    pass_to_dependency: dict[str, Any] = Field(default_factory=dict)


async def simple_json_processor(response: aiohttp.ClientResponse, request) -> ProcessedResponse:
    if response.status >= 400:
        ok = False
        content = []
        error = response.reason
    else:
        resp_json: dict[str, Any] | list[dict[str, Any]] = await response.json()
        error = None
        ok = True
        if isinstance(resp_json, dict):
            content = [resp_json]
        else:
            content = resp_json

    return ProcessedResponse(ok=ok, status=response.status, content=content, error=error)

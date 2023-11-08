import asyncio
from typing import Any

import aiohttp

from .queue import RequestQueue
from .request import Request
from .response import ProcessedResponse


class Session:
    def __init__(self, queue: RequestQueue, timeout: int = 60) -> None:
        self.queue = queue
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    async def process_queue(self, batch_size: int) -> list[ProcessedResponse]:
        all_responses: list[ProcessedResponse] = []
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            while True:
                batch: list[Request] = []
                for _ in range(batch_size):
                    try:
                        batch.append(self.queue.get())
                    except asyncio.QueueEmpty:
                        break

                if not batch:
                    break

                tasks = [asyncio.create_task(self.send(session, request) for request in batch)]
                processed_responses: list[ProcessedResponse] = await asyncio.gather(*tasks)

                for response in processed_responses:
                    # Add deferred requests that depend on this response if any
                    await self.queue.add_deferred(response.request.id)
                    # Add new requests created by the response processor
                    for new_request in response.chain:
                        await self.queue.add(new_request)
        return all_responses

    def _prepare_request(self, request: Request) -> dict[str, Any]:
        params = {
            "method": request.method,
            "url": request.url,
            "headers": request.headers,
        }
        if request.body:
            params["json"] = request.body
        elif request.form_data:
            params["data"] = request.form_data
        return params

    async def send(self, session: aiohttp.ClientSession, request: Request) -> ProcessedResponse:
        params = self._prepare_request(request)
        async with session.request(**params) as resp:
            return await request.process_response(resp)

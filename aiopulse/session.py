import asyncio
import logging
from typing import Any

import aiohttp
from pydantic import ValidationError

from .factory import RequestFactory
from .queue import RequestQueue
from .request import Request
from .response import ProcessedResponse


class Session:
    logger = logging.getLogger(__name__)

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.logger.debug(f"<Session> object created with timeout {timeout}s")

    async def process_queue(self, queue: RequestQueue, batch_size: int, factory: RequestFactory) -> list[ProcessedResponse]:
        self.logger.info(f"Triggering queue processing. Batch size = {batch_size}")
        all_responses: list[ProcessedResponse] = []
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            while True:
                batch: list[Request] = []
                for _ in range(batch_size):
                    try:
                        batch.append(queue.get())
                    except asyncio.QueueEmpty:
                        break

                if not batch:
                    break

                tasks = [asyncio.create_task(self.send(session, request) for request in batch)]
                processed_responses: list[ProcessedResponse] = await asyncio.gather(*tasks)
                self.logger.info("Finished request batch. Processing responses...")
                for response in processed_responses:
                    # Add deferred requests that depend on this response if any
                    await queue.add_deferred(response.request.id)
                    # Add new requests created by the response processor
                    if response.chain:
                        await self._add_chained_requests(queue, factory, response)
        return all_responses

    async def _add_chained_requests(self, queue: RequestQueue, factory: RequestFactory, response: ProcessedResponse) -> None:
        self.logger.info(f"Adding chained requests created by request id {response.request.id}")
        try:
            await queue.build_queue(factory, response.chain)
            self.logger.info(f"Chained requests created by request id {response.request.id} added to queue")
        except (ValidationError, ValueError) as err:
            self.logger.error(f"Could not build chained requests for request of id {response.request.id}. Skipping rest of chain. Error: {str(err)}")

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

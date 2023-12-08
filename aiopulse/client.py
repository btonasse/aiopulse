import asyncio
import logging
from typing import Any

import aiohttp
from pydantic import BaseModel, ValidationError

from .factory import RequestFactory
from .queue import RequestQueue
from .request import Request
from .response import ProcessedResponse


class ProcessingResult(BaseModel):
    request: Request
    response: ProcessedResponse | None


class Client:
    logger = logging.getLogger(__name__)

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.logger.debug(f"Client initialized with timeout {timeout}s")

    async def process_queue(self, session: aiohttp.ClientSession, queue: RequestQueue, batch_size: int, factory: RequestFactory) -> list[ProcessingResult]:
        self.logger.info(f"Triggering queue processing. Batch size = {batch_size}")
        results: list[ProcessingResult] = []
        while True:
            batch: list[Request] = []
            for _ in range(batch_size):
                try:
                    batch.append(queue.get())
                except asyncio.QueueEmpty:
                    break

            if not batch:
                self.logger.info("No more requests to send.")
                break
            tasks = [asyncio.create_task(self.send(session, request)) for request in batch]
            processed_responses: list[ProcessedResponse | None] = await asyncio.gather(*tasks)
            self.logger.info("Finished request batch.")
            for i, response in enumerate(processed_responses):
                request = batch[i]
                results.append(ProcessingResult(request=request, response=response))
                # Do not process dependent requests if there has been an error
                if not response or not response.ok:
                    self.logger.warning("Request with id %s failed. Any dependent requests will be skipped.", request.id)
                    continue
                # Add new requests created by the response processor
                if response.chain:
                    self.logger.info("Adding chained requests created by request id %s", request.id)
                    queue.defer(response.chain, request.id)
                # Add deferred requests that depend on this response if any
                await queue.add_deferred(factory, request.id, response.pass_to_dependency)

        return results

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

    async def send(self, session: aiohttp.ClientSession, request: Request) -> ProcessedResponse | None:
        params = self._prepare_request(request)
        self.logger.info(f"Sending {request.method} request with id {request.id} to {request.url}...")
        try:
            resp = await session.request(timeout=self.timeout, **params)
            self.logger.info("Request id %s successful. Processing response...", request.id)
            return await request.process_response(resp)
        except aiohttp.ClientError as err:
            msg = f"{type(err).__name__}: {str(err)}"
            self.logger.error("Request id %s failed with error '%s'", request.id, msg)

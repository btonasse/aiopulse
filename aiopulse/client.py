import asyncio
import logging
from typing import Any

import aiohttp
from pydantic import BaseModel

from .factory import RequestFactory
from .queue import RequestQueue
from .request import Request
from .response import ProcessedResponse


class ProcessingResult(BaseModel):
    request: Request
    response: ProcessedResponse | None


class Aiopulse:
    logger = logging.getLogger(__name__)

    def __init__(self, timeout: int = 60) -> None:
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.queue = RequestQueue()
        self.factory = RequestFactory()
        self.logger.debug(f"Aiopulse client initialized with timeout {timeout}s")

    async def process_queue(self, session: aiohttp.ClientSession, batch_size: int) -> list[ProcessingResult]:
        self.logger.info(f"Triggering queue processing. Batch size = {batch_size}")
        results: list[ProcessingResult] = []
        while True:
            batch: list[Request] = []
            for _ in range(batch_size):
                try:
                    batch.append(self.queue.get())
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

                if response and response.ok:
                    # Add new requests created by the response processor
                    if response.chain:
                        self.logger.info("Adding chained requests created by request id %s", request.id)
                        self.queue.defer(response.chain, request.id)
                    # Add deferred requests that depend on this response if any
                    try:
                        await self.add_deferred_to_queue(request.id, response.pass_to_dependency)
                    except ValueError as err:
                        self.logger.warning("Failed to add dependent requests for request id %s. Error: %s.", request.id, err)

                # Do not process dependent requests if there has been an error
                else:
                    self.logger.warning("Request with id %s failed. Any dependent requests will be skipped.", request.id)

                results.append(ProcessingResult(request=request, response=response))

        return results

    async def build_and_add_to_queue(self, data: dict[str, Any], chain_keyword: str = "chain", extra_args: dict[str, Any] = dict()) -> None:
        request = self.factory.build_request(data, extra_input_args=extra_args)
        await self.queue.add(request)
        chain = data.get(chain_keyword)
        if chain:
            self.queue.defer(chain, request.id)

    async def add_deferred_to_queue(self, dependency: int, extra_input_args: dict[str, Any] = dict()) -> None:
        self.logger.info("Fetching deferred requests for dependency %s...", dependency)
        deferred = self.queue.get_deferred(dependency)
        if deferred:
            self.logger.info("Found %s dependent requests. %s extra args will be passed to chained data.", len(deferred), len(extra_input_args))
            for payload in deferred:
                await self.build_and_add_to_queue(payload, extra_args=extra_input_args)

    async def send(self, session: aiohttp.ClientSession, request: Request) -> ProcessedResponse | None:
        params = request.prepare()
        self.logger.info(f"Sending {request.method} request with id {request.id} to {request.url}...")
        try:
            resp = await session.request(timeout=self.timeout, **params)
            self.logger.info("Request id %s successful. Processing response...", request.id)
            return await request.process_response(resp)
        except aiohttp.ClientError as err:
            msg = f"{type(err).__name__}: {str(err)}"
            self.logger.error("Request id %s failed with error '%s'", request.id, msg)

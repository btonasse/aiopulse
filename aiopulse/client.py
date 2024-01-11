import asyncio
import logging
from typing import Any

import aiohttp
from pydantic import BaseModel

from .factory import RequestFactory
from .mapping import RequestBuildMapping
from .queue import RequestQueue
from .request import Request
from .response import ProcessedResponse


class ProcessingResult(BaseModel):
    request: Request
    response: ProcessedResponse


class Aiopulse:
    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        self.queue = RequestQueue()
        self.factory = RequestFactory()
        self.logger.debug("Aiopulse client initialized")

    def register_mapping(self, mapping: RequestBuildMapping) -> None:
        self.factory.register_mapping(mapping)

    async def build_and_add_to_queue(self, data: dict[str, Any], chain_keyword: str = "chain", extra_args: dict[str, Any] = dict()) -> None:
        await self.queue.build_and_add(self.factory, data, chain_keyword=chain_keyword, extra_args=extra_args)

    def set_transformer_args(self, mapping_title: str, **args: dict[str, Any]) -> None:
        self.factory.set_transformer_args(mapping_title, **args)

    async def process_queue(self, session: aiohttp.ClientSession, batch_size: int, timeout: int = 60) -> list[ProcessingResult]:
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
            tasks = [asyncio.create_task(self.send(session, request, timeout)) for request in batch]
            processed_responses: list[ProcessedResponse] = await asyncio.gather(*tasks)
            self.logger.info("Finished request batch.")
            for i, response in enumerate(processed_responses):
                request = batch[i]

                if response.ok:
                    # Add new requests created by the response processor
                    if response.chain:
                        self.logger.info("Adding chained requests created by request id %s", request.id)
                        self.queue.defer(response.chain, request.id)
                    # Add deferred requests that depend on this response if any
                    try:
                        await self.queue.add_deferred(self.factory, request.id, response.pass_to_dependency)
                    except ValueError as err:
                        self.logger.warning("Failed to add dependent requests for request id %s. Error: %s.", request.id, err)

                # Do not process dependent requests if there has been an error
                else:
                    self.logger.warning("Request with id %s failed. Any dependent requests will be skipped.", request.id)

                results.append(ProcessingResult(request=request, response=response))

        return results

    async def send(self, session: aiohttp.ClientSession, request: Request, timeout: int = 60) -> ProcessedResponse:
        params = request.prepare()
        self.logger.info(f"Sending {request.method} request with id {request.id} to {request.url}...")
        try:
            resp = await session.request(timeout=aiohttp.ClientTimeout(total=timeout), **params)
            self.logger.info("Request id %s successful. Processing response...", request.id)
            return await request.process_response(resp)
        except aiohttp.ClientError as err:
            msg = f"{type(err).__name__}: {str(err)}"
            self.logger.error("Request id %s failed with error '%s'", request.id, msg)
            return ProcessedResponse(error=msg, ok=False, content=[])

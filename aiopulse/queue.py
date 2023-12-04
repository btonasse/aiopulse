import asyncio
import logging
from typing import Any

from .factory import RequestFactory
from .request import Request


class RequestQueue:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._queue: asyncio.Queue[Request] = asyncio.Queue()
        self._deferred_requests: dict[int, list[Request]] = dict()
        self.logger.debug("RequestQueue initialized.")

    async def add(self, request: Request) -> None:
        await self._queue.put(request)
        self.logger.info(f"Added request with id {request.id} to queue")

    def get(self) -> Request:
        req = self._queue.get_nowait()
        self.logger.info(f"Retrieved request with id {req.id} from queue")
        return req

    async def build_queue(self, factory: RequestFactory, data: list[dict[str, Any]], dependency: int | None = None) -> None:
        """Iterate through the inputs to build new `Request` instances and add them to the queue.

        Each input payload can define nested, dependent requests in the `chain` property.
        If such a chain of requests is found, the method will recurse and add the new `Request` objects to `self._deferred_requests` instead of directly to the queue.

        Args:
            factory (RequestFactory): The factory class for building the requests
            data (list[dict[str, Any]]): A list of payloads to build the requests, potentially nested via the `chain` property
            dependency (int | None, optional): When recursing, the `id` of the parent `Request` is passed as this argument so we can keep track of which parent a child `Request` depends on. Defaults to None.
        """
        self.logger.info(f"Building request queue. Dependency: {dependency}")
        if not isinstance(data, list):
            err = "Failed building queue: input data has to be a list/array"
            raise TypeError(err)
        for payload in data:
            request = factory.build_request(payload)

            if dependency is not None:
                self.defer(request, dependency)
            else:
                await self.add(request)

            chain = payload.get("chain")
            if chain:
                self.logger.info(f"Request with id {request.id} has chained requests. Building them recursively...")
                await self.build_queue(factory, chain, request.id)

    def defer(self, request: Request, dependency: int) -> None:
        self.logger.info(f"Request id {request.id} has a dependency (id {dependency}). Adding to deferred queue...")
        deferred = self._deferred_requests.get(dependency)
        if not deferred:
            self._deferred_requests[dependency] = [request]
        else:
            self._deferred_requests[dependency].append(request)

    async def add_deferred(self, dependency: int) -> None:
        self.logger.info(f"Fetching deferred requests for dependency {dependency}...")
        deferred = self._deferred_requests.get(dependency)
        if deferred:
            self.logger.info(f"Found {len(deferred)} dependent requests.")
            for request in deferred:
                await self.add(request)

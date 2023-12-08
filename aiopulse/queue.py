import asyncio
import logging
from typing import Any

from .factory import RequestFactory
from .request import Request


class RequestQueue:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._queue: asyncio.Queue[Request] = asyncio.Queue()
        self._deferred_requests: dict[int, list[dict[str, Any]]] = dict()
        self.logger.debug("RequestQueue initialized.")

    async def add(self, request: Request) -> None:
        await self._queue.put(request)
        self.logger.info(f"Added request with id {request.id} to queue")

    def get(self) -> Request:
        req = self._queue.get_nowait()
        self.logger.info(f"Retrieved request with id {req.id} from queue")
        return req

    async def build_queue(self, factory: RequestFactory, data: list[dict[str, Any]], extra_args: dict[str, Any] = dict()) -> None:
        """Iterate through the inputs to build new `Request` instances and add them to the queue.

        Each input payload can define nested, dependent requests in the `chain` property.
        If such a chain of requests is found, they will be added to `self._deferred_requests` to be built and added to the queue later.

        Args:
            factory (RequestFactory): The factory class for building the requests
            data (list[dict[str, Any]]): A list of payloads to build the requests, potentially nested via the `chain` property
            extra_args (dict[str, Any]): Arguments passed by dependencies down to the request chain. They are merged with the payload before building the request.
        """
        self.logger.info("Building request queue...")
        if not isinstance(data, list):
            err = "Failed building queue: input data has to be a list/array"
            raise TypeError(err)
        for payload in data:
            try:
                request = factory.build_request(payload | extra_args)
                await self.add(request)
                chain = payload.get("chain")
                if chain:
                    self.defer(chain, request.id)
            except ValueError as err:
                self.logger.error("Failed to build request, skipping it and any chained requests - %s: %s", err.__class__.__name__, err)

    def defer(self, chain: list[dict[str, Any]], dependency: int) -> None:
        self.logger.info("Request id %s has %s dependent requests. Adding to deferred queue...", dependency, len(chain))
        self._deferred_requests[dependency] = chain

    async def add_deferred(self, factory: RequestFactory, dependency: int, extra_args: dict[str, Any] = dict()) -> None:
        self.logger.info("Fetching deferred requests for dependency %s...", dependency)
        deferred = self._deferred_requests.get(dependency)
        if deferred:
            self.logger.info("Found %s dependent requests. %s extra args will be passed to chained data.", len(deferred), len(extra_args))
            await self.build_queue(factory, deferred, extra_args)

    def request_count(self) -> int:
        return self._queue.qsize()

    def deferred_count(self) -> int:
        # Todo recurse and get all
        return sum(len(reqs) for reqs in self._deferred_requests.values())

    def total_request_count(self) -> int:
        return self.request_count() + self.deferred_count()

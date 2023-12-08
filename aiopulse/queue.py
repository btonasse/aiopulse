import asyncio
import logging
from typing import Any

from .factory import RequestFactory
from .request import Counter, Request


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
            if dependency is not None:
                new_id = Counter()()
                self.defer(payload, new_id, dependency)
            else:
                request = factory.build_request(payload)

                await self.add(request)
                new_id = request.id

            chain = payload.get("chain")
            if chain:
                self.logger.info(f"Request with id {new_id} has chained requests. Adding them to deferred queue...")
                await self.build_queue(factory, chain, new_id)

    def defer(self, payload: dict[str, Any], deferred_id: int, dependency: int) -> None:
        self.logger.info(f"Deferred request id {deferred_id} has a dependency (id {dependency}). Adding to deferred queue...")
        payload["id"] = deferred_id  # Make sure the generated id will be used to build the request
        deferred = self._deferred_requests.get(dependency)
        if not deferred:
            self._deferred_requests[dependency] = [payload]
        else:
            self._deferred_requests[dependency].append(payload)

    async def add_deferred(self, factory: RequestFactory, dependency: int, extra_args: dict[str, Any] = dict()) -> None:
        self.logger.info(f"Fetching deferred requests for dependency {dependency}...")
        deferred = self._deferred_requests.get(dependency)
        if deferred:
            self.logger.info(f"Found {len(deferred)} dependent requests. {len(extra_args)} extra args will be passed to chained data.")
            for payload in deferred:
                # Todo test this!
                new_payload = payload | extra_args
                try:
                    new_request = factory.build_request(new_payload)
                    await self.add(new_request)
                except Exception as e:
                    self.logger.error("Could not build chained request with id %s. Skipping.", payload.get("id"))

    def total_request_count(self) -> int:
        in_queue = self._queue.qsize()
        deferred = sum(len(reqs) for reqs in self._deferred_requests.values())
        return in_queue + deferred

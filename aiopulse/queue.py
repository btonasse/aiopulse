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

    def get_deferred(self, parent_id: int) -> list[dict[str, Any]]:
        deferred = self._deferred_requests.get(parent_id, [])
        self.logger.info(f"Retrieved {len(deferred)} from queue")
        return deferred

    def defer(self, chain: list[dict[str, Any]], dependency: int) -> None:
        self.logger.info("Request id %s has %s dependent requests. Adding to deferred queue...", dependency, len(chain))
        dependencies = self._deferred_requests.get(dependency)
        if dependencies:
            self._deferred_requests[dependency].extend(chain)
        else:
            self._deferred_requests[dependency] = chain

    async def build_and_add(self, factory: RequestFactory, data: dict[str, Any], chain_keyword: str = "chain", extra_args: dict[str, Any] = dict()) -> None:
        request = factory.build_request(data, extra_input_args=extra_args)
        await self.add(request)
        chain = data.get(chain_keyword)
        if chain:
            self.defer(chain, request.id)

    async def add_deferred(self, factory: RequestFactory, dependency: int, extra_input_args: dict[str, Any] = dict()) -> None:
        self.logger.info("Fetching deferred requests for dependency %s...", dependency)
        deferred = self.get_deferred(dependency)
        if deferred:
            self.logger.info("Found %s dependent requests. %s extra args will be passed to chained data.", len(deferred), len(extra_input_args))
            for payload in deferred:
                await self.build_and_add(factory, payload, extra_args=extra_input_args)

    def request_count(self) -> int:
        return self._queue.qsize()

    def deferred_count(self) -> int:
        def _count_recursively(deferred_list: list[dict[str, Any]]) -> int:
            count = 0
            for payload in deferred_list:
                count += 1
                chain: list[dict[str, Any]] | None = payload.get("chain")
                if chain:
                    count += _count_recursively(chain)

            return count

        return _count_recursively([deferred for deferred_list in self._deferred_requests.values() for deferred in deferred_list])

    def total_request_count(self) -> int:
        return self.request_count() + self.deferred_count()

import asyncio

import pytest

from aiopulse import RequestQueue


@pytest.fixture
def queue():
    return RequestQueue()


class TestQueue:
    async def test_add(self, queue: RequestQueue, dummy_request):
        await queue.add(dummy_request())
        assert queue._queue.qsize() == 1

    async def test_get(self, queue: RequestQueue, dummy_request):
        dummy = dummy_request()
        await queue._queue.put(dummy)
        assert queue._queue.qsize() == 1
        req = queue.get()
        assert req is dummy
        with pytest.raises(asyncio.QueueEmpty):
            queue.get()

    async def test_total_count(self, queue: RequestQueue, dummy_request, payload):
        await queue.add(dummy_request())
        await queue.add(dummy_request())
        queue._deferred_requests[1] = [payload, payload, payload]
        queue._deferred_requests[2] = [payload, {"chain": [payload, payload]}]
        assert queue.total_request_count() == 9

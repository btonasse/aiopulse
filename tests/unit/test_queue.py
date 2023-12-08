import asyncio

import pytest

from aiopulse import RequestQueue


@pytest.fixture
def queue():
    return RequestQueue()


@pytest.fixture
def nested_payloads(payload):
    copy = dict(payload)
    payload["chain"] = [copy]
    return [payload, copy]


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

    async def test_build_queue(self, queue: RequestQueue, nested_payloads, dummy_factory, payload):
        with pytest.raises(TypeError):
            await queue.build_queue(dummy_factory, payload)
        await queue.build_queue(dummy_factory, nested_payloads)
        assert queue._queue.qsize() == 2
        assert len(queue._deferred_requests) == 1
        deferred = queue._deferred_requests.get(1)
        assert isinstance(deferred, list)

    async def test_total_count(self, queue: RequestQueue, dummy_request, payload):
        await queue.add(dummy_request())
        await queue.add(dummy_request())
        queue._deferred_requests[1] = [payload, payload, payload]
        queue._deferred_requests[2] = [payload, {"chain": [payload, payload]}]
        assert queue.total_request_count() == 9

    async def test_add_deferred(self, queue: RequestQueue, payload, dummy_factory, dummy_request):
        req1 = dummy_request(1)
        req2 = dummy_request(2)
        await queue.add(req1)
        await queue.add(req2)
        queue._deferred_requests[1] = [payload]
        await queue.add_deferred(dummy_factory, 1)
        assert queue._queue.qsize() == 3

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

    async def test_build_queue(self, queue: RequestQueue, nested_payloads, dummy_factory):
        await queue.build_queue(dummy_factory, nested_payloads)
        assert queue._queue.qsize() == 2
        assert len(queue._deferred_requests) == 1
        assert queue._deferred_requests.get(1)

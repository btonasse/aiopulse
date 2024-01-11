import asyncio
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest

from aiopulse import Aiopulse, ProcessedResponse, RequestQueue


@pytest.fixture
def completion_order():
    return []


@pytest.fixture
async def mock_send(dummy_processed_response, completion_order):
    async def patched_send(self, session, request):
        delay = request.body.get("delay", 0.01)
        resp = dummy_processed_response()
        resp.content = [{"delay": delay}]
        resp.ok = True
        await asyncio.sleep(delay)
        completion_order.append(request.id)
        return resp

    return patched_send


@pytest.fixture
async def mock_request_method(request):
    params = getattr(request, "param", dict())
    mock_method = AsyncMock(aiohttp.ClientSession.request)
    if params.get("error"):
        mock_method.side_effect = aiohttp.ClientError("Some random exception")
    else:
        mock_method.return_value = MagicMock(aiohttp.ClientResponse)
    return mock_method


class TestClient:
    @pytest.mark.parametrize(
        "dummy_queue, expected_order",
        [
            ({"delay": [0.01, 0.001]}, [2, 1]),
            ({"delay": [0.001, 0.001]}, [1, 2]),
        ],
        indirect=["dummy_queue"],
    )
    async def test_process_queue(self, mock_send, dummy_queue, loop, monkeypatch, expected_order, completion_order):
        client = Aiopulse()
        client.queue = dummy_queue
        monkeypatch.setattr(Aiopulse, "send", mock_send)
        async with aiohttp.ClientSession() as session:
            results = await client.process_queue(session, 10, 1)
        assert len(results) == 2
        assert completion_order == expected_order

    @pytest.mark.parametrize(
        "mock_request_method, dummy_request, expected_status",
        [
            ({"error": True}, {"error": "Some random exception", "status": None}, None),
            ({"error": False}, {}, 200),
        ],
        indirect=["mock_request_method", "dummy_request"],
    )
    async def test_send(self, mock_request_method, monkeypatch, dummy_request, expected_status, loop):
        client = Aiopulse()
        monkeypatch.setattr(aiohttp.ClientSession, "request", mock_request_method)
        async with aiohttp.ClientSession() as session:
            resp = await client.send(session, dummy_request())
        assert isinstance(resp, ProcessedResponse)
        assert resp.status == expected_status

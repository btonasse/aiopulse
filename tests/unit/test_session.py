import asyncio

import pytest

from aiopulse import RequestQueue, Session


@pytest.fixture
def completion_order():
    return []


@pytest.fixture
async def mock_send(dummy_processed_response, completion_order):
    async def patched_send(self, session, request):
        delay = request.body.get("delay", 0.01)
        resp = dummy_processed_response()
        resp.content = [{"delay": delay}]
        resp.request = request
        await asyncio.sleep(delay)
        completion_order.append(request.id)
        return resp

    return patched_send


class TestSession:
    @pytest.mark.parametrize(
        "dummy_request, payload_type",
        [
            ({"body": {"some": "thing"}}, "json"),
            ({"form_data": {"some": "thing"}}, "data"),
        ],
        indirect=["dummy_request"],
    )
    def test_prepare_request(self, dummy_request, payload_type):
        session = Session()
        req = session._prepare_request(dummy_request())
        assert not (req.get("json") is not None and req.get("data") is not None)
        assert req.get(payload_type) == {"some": "thing"}

    @pytest.mark.parametrize(
        "dummy_queue, expected_order",
        [
            ({"delay": [0.01, 0.001, 0.0001]}, [2, 1, 3]),
            ({"delay": [0.001, 0.001, 0.0001]}, [1, 2, 3]),
        ],
        indirect=["dummy_queue"],
    )
    async def test_process_queue(self, dummy_queue: RequestQueue, dummy_factory, mock_send, loop, monkeypatch, expected_order, completion_order):
        session = Session(1)
        monkeypatch.setattr(Session, "send", mock_send)
        resps = await session.process_queue(dummy_queue, 10, dummy_factory)
        assert len(resps) == 3
        assert completion_order == expected_order

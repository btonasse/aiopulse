from typing import Any
from unittest import mock

import aiohttp
import pytest

from aiopulse import Client, GenericInputSchema, ProcessedResponse, Request, RequestFactory, RequestQueue


@pytest.fixture
def payload(request) -> dict[str, Any]:
    data = {
        "description": "Some description",
        "url": "https://www.somehost.com/somepath",
        "method": "POST",
        "headers": {"x-csrf-token": "blablablaba="},
        "body": {"heyjude": "dontmakemecry", "lalala": 123},
        "query_params": {"someparam": "1", "otherparam": "2"},
    }
    params = getattr(request, "param", dict())
    for k, v in params.items():
        if k == "remove_key" and v in data.keys():
            del data[v]
        else:
            data[k] = v
    return data


@pytest.fixture
def dummy_processor():
    def func():
        return 42

    return func


@pytest.fixture
def dummy_input_data(payload) -> GenericInputSchema:
    schema = mock.Mock(GenericInputSchema)
    schema.configure_mock(**payload)
    return schema


@pytest.fixture
def dummy_response() -> aiohttp.ClientResponse:
    return mock.Mock(aiohttp.ClientResponse)


@pytest.fixture(scope="function")
def dummy_request(request, dummy_processed_response):
    def _make(id: int = 1):
        m = mock.Mock(Request)
        m.id = id
        params = getattr(request, "param", dict())
        m.body = params.get("body") or dict()
        m.url = mock.Mock()
        m.query_params = mock.Mock()
        m.method = mock.Mock()
        m.headers = dict()
        m.form_data = params.get("form_data") or dict()
        m.process_response.return_value = dummy_processed_response()
        return m

    return _make


@pytest.fixture
def dummy_factory(dummy_request) -> RequestFactory:
    factory = mock.MagicMock(RequestFactory)
    factory.build_request.return_value = dummy_request()
    return factory


@pytest.fixture
def dummy_client() -> Client:
    s = mock.Mock(Client)
    return s


@pytest.fixture
async def dummy_queue(request, dummy_request) -> RequestQueue:
    params = getattr(request, "param", dict())
    q = RequestQueue()
    r1 = dummy_request()
    r1.body["delay"] = params.get("delay", (0.01, 0.01))[0]
    await q._queue.put(r1)
    r2 = dummy_request(2)
    r2.body["delay"] = params.get("delay", (0.01, 0.01))[1]
    await q._queue.put(r2)
    return q


@pytest.fixture
def dummy_processed_response(request):
    def _make():
        m = mock.MagicMock(ProcessedResponse)
        params = getattr(request, "param", dict())
        m.chain = list()
        m.pass_to_dependency = dict()
        m.error = None
        return m

    return _make

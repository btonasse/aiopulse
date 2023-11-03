from typing import Any
from unittest import mock

import aiohttp
import pytest

from aiopulse.request import Request
from aiopulse.request.factory import RequestFactory
from aiopulse.request.schema import GenericInputSchema
from aiopulse.request.transformer import GenericTransformer


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
    params = getattr(request, "param", None)
    if not params:
        return data
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
def dummy_transformer(payload) -> GenericTransformer:
    transformer = mock.MagicMock(GenericTransformer)
    payload["extra_info"] = 1234
    transformer.transform_input.return_value = payload
    return transformer


@pytest.fixture
def dummy_transformer2(payload) -> GenericTransformer:
    transformer = mock.MagicMock(GenericTransformer)
    payload["even_more_extra_info"] = 42
    transformer.transform_input.return_value = payload
    return transformer


@pytest.fixture
def dummy_input_data(payload) -> GenericInputSchema:
    schema = mock.Mock(GenericInputSchema)
    schema.configure_mock(**payload)
    return schema


@pytest.fixture
def dummy_response() -> aiohttp.ClientResponse:
    return mock.Mock(aiohttp.ClientResponse)


@pytest.fixture
def dummy_request() -> Request:
    m = mock.Mock(Request)
    m.id = 1
    return m


@pytest.fixture
def dummy_factory(dummy_request) -> RequestFactory:
    factory = mock.MagicMock(RequestFactory)
    factory.build_request.return_value = dummy_request
    return factory

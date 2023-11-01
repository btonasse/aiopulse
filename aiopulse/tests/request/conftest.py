from typing import Any

import pytest

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
def dummy_transformer() -> GenericTransformer:
    return GenericTransformer()


@pytest.fixture
def dummy_input_data(payload) -> GenericInputSchema:
    return GenericInputSchema(**payload)

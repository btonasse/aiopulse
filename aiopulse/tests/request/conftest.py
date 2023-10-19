from typing import Any

import pytest


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

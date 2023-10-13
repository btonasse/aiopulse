from contextlib import nullcontext as does_not_raise
from typing import Any

import pytest
import yarl
from pydantic import ValidationError

from reqme.request import Method
from reqme.request.schema import GenericSchema


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


class TestGenericSchema:
    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"url": "asdasd"}, does_not_raise()),
            ({"url": 123}, pytest.raises(ValidationError)),
            ({"remove_key": "url"}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_validate_url(self, payload, expectation):
        with expectation:
            params = GenericSchema(**payload)
            assert isinstance(params.url, yarl.URL)

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"method": "blablablo"}, pytest.raises(ValidationError)),
            ({"remove_key": "method"}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_validate_method(self, payload, expectation):
        with expectation:
            params = GenericSchema(**payload)
            assert isinstance(params.method, Method)
            assert params.method.value == "post"

    def test_is_match(self, payload):
        assert GenericSchema.is_match(payload)

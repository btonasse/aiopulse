from contextlib import nullcontext as does_not_raise

import pytest
import yarl
from pydantic import ValidationError

from aiopulse import GenericInputSchema
from aiopulse.request import Method


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
            params = GenericInputSchema(**payload)
            assert isinstance(params.url, yarl.URL)

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"method": "post"}, does_not_raise()),
            ({"method": "blablablo"}, pytest.raises(ValidationError)),
            ({"remove_key": "method"}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_validate_method(self, payload, expectation):
        with expectation:
            params = GenericInputSchema(**payload)
            assert isinstance(params.method, Method)
            assert params.method.value == "post"

    def test_json_generation(self):
        with does_not_raise():
            assert print(GenericInputSchema.model_json_schema())

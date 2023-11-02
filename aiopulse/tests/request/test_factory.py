from contextlib import nullcontext as does_not_raise

import pytest
import yarl
from pydantic import ValidationError

from aiopulse.request import Request
from aiopulse.request.factory import RequestFactory
from aiopulse.request.schema import GenericInputSchema


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def setup_factory(factory: RequestFactory, dummy_processor, dummy_transformer):
    factory.mappings = [{"schema": GenericInputSchema, "response_processor": dummy_processor, "transformers": [dummy_transformer]}]
    return factory


class TestRequestFactory:
    def test_register(self, factory: RequestFactory, dummy_processor, dummy_transformer):
        factory.register_mapping(schema=GenericInputSchema, transformers=[dummy_transformer], response_processor=dummy_processor)
        assert len(factory.mappings) == 1
        assert factory.mappings[0]["schema"] is GenericInputSchema
        assert factory.mappings[0]["transformers"] == [dummy_transformer]
        assert factory.mappings[0]["response_processor"] == dummy_processor

    def test_apply_transformers(self, payload, factory: RequestFactory, dummy_transformer, dummy_transformer2):
        t = factory.apply_transforms(data=payload, transformers=[dummy_transformer, dummy_transformer2])
        assert "extra_info" in t.keys()
        assert "even_more_extra_info" in t.keys()

    def test_request_build(self, setup_factory: RequestFactory, payload):
        req = setup_factory.build_request(payload)
        assert isinstance(req, Request)

from contextlib import nullcontext as does_not_raise

import pytest
import yarl
from pydantic import ValidationError

from aiopulse.request.factory import RequestFactory
from aiopulse.request.schema import GenericInputSchema


@pytest.fixture
def factory():
    return RequestFactory()


class TestRequestFactory:
    def test_register(self, factory: RequestFactory, dummy_processor, dummy_transformer):
        factory.register_mapping(GenericInputSchema, dummy_transformer, dummy_processor)
        assert len(factory.mappings) == 1
        assert factory.mappings[0]["schema"] is GenericInputSchema
        assert factory.mappings[0]["transformer"] == dummy_transformer
        assert factory.mappings[0]["response_processor"] == dummy_processor

    # Todo test build request

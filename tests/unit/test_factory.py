from typing import Any

import pytest

from aiopulse import GenericInputSchema, Request, RequestFactory, RequestFactoryMapping, TransformerBase


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def always_true():
    def _func(arg):
        return True

    return _func


@pytest.fixture
def dummy_transformer():
    class NoOp(TransformerBase):
        def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
            return input_data

    return NoOp


@pytest.fixture
def dummy_transformer_with_args():
    class WithArgs(TransformerBase):
        some_arg: int

        def transform_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
            input_data["some_arg"] = self.some_arg
            return input_data

    return WithArgs


@pytest.fixture
def dummy_mapping(dummy_processor, always_true, dummy_transformer):
    return RequestFactoryMapping(title="Dummy", description="Dummy mapping", input_schema=GenericInputSchema, response_processor=dummy_processor, transformers=[dummy_transformer], is_match=always_true)


@pytest.fixture
def setup_factory(factory: RequestFactory, dummy_mapping):
    factory.mappings = [dummy_mapping]
    return factory


class TestRequestFactory:
    def test_register(self, factory: RequestFactory, dummy_processor, dummy_mapping, always_true, dummy_transformer):
        factory.register_mapping(dummy_mapping)
        assert len(factory.mappings) == 1
        assert factory.mappings[0].input_schema is GenericInputSchema
        assert factory.mappings[0].transformers == [dummy_transformer]
        assert factory.mappings[0].response_processor == dummy_processor
        assert factory.mappings[0].is_match == always_true

    def apply_extra_args(self, payload, dummy_transformer_with_args):
        factory = RequestFactory()
        factory.set_transformer_args(some_arg=1)
        transformed = factory.apply_transforms(payload, [dummy_transformer_with_args])
        assert "some_arg" in transformed.keys() and transformed["some_arg"] == 1

    def test_request_build(self, setup_factory: RequestFactory, payload):
        req = setup_factory.build_request(payload)
        assert isinstance(req, Request)

    def test_is_match(self, payload, dummy_mapping: RequestFactoryMapping):
        assert dummy_mapping.is_match(payload)

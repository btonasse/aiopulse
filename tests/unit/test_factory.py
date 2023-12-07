import pytest

from aiopulse import GenericInputSchema, Request, RequestFactory, RequestFactoryMapping


@pytest.fixture
def factory():
    return RequestFactory()


@pytest.fixture
def always_true():
    def _func(arg):
        return True

    return _func


@pytest.fixture
def dummy_mapping(dummy_processor, dummy_transformer, always_true):
    return RequestFactoryMapping(input_schema=GenericInputSchema, response_processor=dummy_processor, transformers=[dummy_transformer], is_match=always_true)


@pytest.fixture
def setup_factory(factory: RequestFactory, dummy_mapping):
    factory.mappings = [dummy_mapping]
    return factory


class TestRequestFactory:
    def test_register(self, factory: RequestFactory, dummy_processor, dummy_transformer, dummy_mapping, always_true):
        factory.register_mapping(dummy_mapping)
        assert len(factory.mappings) == 1
        assert factory.mappings[0].input_schema is GenericInputSchema
        assert factory.mappings[0].transformers == [dummy_transformer]
        assert factory.mappings[0].response_processor == dummy_processor
        assert factory.mappings[0].is_match == always_true

    def test_apply_transformers(self, payload, factory: RequestFactory, dummy_transformer, dummy_transformer2):
        t = factory.apply_transforms(data=payload, transformers=[dummy_transformer, dummy_transformer2])
        assert "extra_info" in t.keys()
        assert "even_more_extra_info" in t.keys()

    def test_request_build(self, setup_factory: RequestFactory, payload):
        req = setup_factory.build_request(payload)
        assert isinstance(req, Request)

    def test_is_match(self, payload, dummy_mapping: RequestFactoryMapping):
        assert dummy_mapping.is_match(payload)

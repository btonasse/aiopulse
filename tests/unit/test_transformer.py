from contextlib import nullcontext as does_not_raise

import pytest
import yarl
from pydantic import ValidationError

from aiopulse import BaseURLTransformer, GenericTransformer


@pytest.fixture
def input_data(request):
    data = {"some_attr": 1234}
    url = getattr(request, "param", None)
    if url:
        data["url"] = url
    return data


class TestGenericTransformer:
    def test_input_output_equality(self, payload):
        assert GenericTransformer().transform_input(payload) == payload


class TestBaseURLTransformer:
    @pytest.mark.parametrize(
        "base_url, expectation",
        [
            ("http://www.basedomain.com", does_not_raise()),
            ("http://www.basedomain.com/some/path", does_not_raise()),
            ("http://www.basedomain.com/some/path?param=1", pytest.raises(ValidationError)),
            ("www.basedomain.com", pytest.raises(ValidationError)),
            ("asdasdad", pytest.raises(ValidationError)),
            (123, pytest.raises(ValidationError)),
        ],
    )
    def test_validate_url(self, base_url, expectation):
        with expectation:
            transformer = BaseURLTransformer(base_url=base_url)
            assert isinstance(transformer.base_url, yarl.URL)
            assert str(transformer.base_url) == base_url

    @pytest.mark.parametrize(
        "base_url, input_data, raise_or_not, expected_url",
        [
            ("http://www.basedomain.com", None, pytest.raises(ValueError), None),
            ("http://www.basedomain.com", "api/v0/endpoint", pytest.raises(ValueError), None),
            ("http://www.basedomain.com", yarl.URL("api/v0/endpoint"), does_not_raise(), "http://www.basedomain.com/api/v0/endpoint"),
            ("http://www.basedomain.com", yarl.URL("api/v0/endpoint?param=1"), does_not_raise(), "http://www.basedomain.com/api/v0/endpoint?param=1"),
            ("http://www.basedomain.com/some/path", yarl.URL("api/v0/endpoint"), does_not_raise(), "http://www.basedomain.com/some/path/api/v0/endpoint"),
            ("http://www.basedomain.com/some/path", yarl.URL("api/v0/endpoint?param=1"), does_not_raise(), "http://www.basedomain.com/some/path/api/v0/endpoint?param=1"),
        ],
        indirect=["input_data"],
    )
    def test_transform_input(self, base_url, input_data, raise_or_not, expected_url):
        with raise_or_not:
            transformed = BaseURLTransformer(base_url=base_url).transform_input(input_data)
            assert all(key in transformed.keys() for key in input_data.keys())
            assert str(transformed["url"]) == expected_url

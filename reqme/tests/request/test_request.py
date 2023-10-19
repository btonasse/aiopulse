from contextlib import nullcontext as does_not_raise

import pytest
import yarl
from pydantic import ValidationError

from reqme.request import Method, Request


@pytest.fixture
def dummy_processor():
    def func():
        return 42

    return func


def test_method_enum():
    assert Method("post") == Method("POST")
    with pytest.raises(ValueError):
        Method("blue")


class TestRequest:
    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({"response_processor": dummy_processor}, does_not_raise()),
            ({}, pytest.raises(ValidationError)),
            ({"response_processor": 42}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_validate_response_processor(self, payload, expectation):
        with expectation:
            assert Request(**payload)._response_processor == dummy_processor

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"url": "asdasd"}, pytest.raises(ValidationError)),
            ({"url": 123}, pytest.raises(ValidationError)),
            ({"remove_key": "url"}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_validate_url(self, payload, expectation, dummy_processor):
        with expectation:
            req = Request(**payload, response_processor=dummy_processor)
            assert isinstance(req.url, yarl.URL)

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"form_data": {"as": 123}}, pytest.raises(ValidationError)),
            ({"remove_key": "body", "form_data": {"as": 123}}, does_not_raise()),
        ],
        indirect=["payload"],
    )
    def test_either_body_or_form(self, payload, expectation, dummy_processor):
        with expectation:
            Request(**payload, response_processor=dummy_processor)

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, "https://www.somehost.com/somepath?someparam=1&otherparam=2"),
            ({"query_params": {}}, "https://www.somehost.com/somepath"),
            ({"remove_key": "query_params"}, "https://www.somehost.com/somepath"),
        ],
        indirect=["payload"],
    )
    def test_add_query_params(self, payload, expectation, dummy_processor):
        assert str(Request(**payload, response_processor=dummy_processor).url) == expectation

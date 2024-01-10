from contextlib import nullcontext as does_not_raise

import pytest
from pydantic import ValidationError
from yarl import URL

from aiopulse import Request
from aiopulse.data_types import Counter, Method, SerializableURL


@pytest.fixture(autouse=True)
def reset_request_counter():
    Counter._counter = 0


def test_method_enum():
    assert Method("post") == Method("POST")
    with pytest.raises(ValueError):
        Method("blue")


class TestRequest:
    @pytest.mark.parametrize(
        "processor, expectation",
        [
            ("callable", does_not_raise()),
            (None, pytest.raises(ValidationError)),
            (42, pytest.raises(ValidationError)),
        ],
    )
    def test_validate_response_processor(self, payload, processor, dummy_processor, expectation):
        with expectation:
            if processor == "callable":
                payload["response_processor"] = dummy_processor
            elif processor:
                payload["response_processor"] = processor
            assert Request(**payload).response_processor == dummy_processor

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
            assert isinstance(req.url, URL)

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

    @pytest.mark.parametrize(
        "payload, expectation",
        [
            ({}, does_not_raise()),
            ({"id": 123}, pytest.raises(ValidationError)),
        ],
        indirect=["payload"],
    )
    def test_id(self, payload, expectation, dummy_processor):
        with expectation:
            assert Request(**payload, response_processor=dummy_processor).id == 1
            assert Request(**payload, response_processor=dummy_processor).id == 2

    @pytest.mark.parametrize(
        "payload, payload_type",
        [
            ({"body": {"some": "thing"}}, "json"),
            ({"form_data": {"some": "thing"}, "remove_key": "body"}, "data"),
        ],
        indirect=["payload"],
    )
    def test_prepare_request(self, payload, dummy_processor, payload_type):
        req = Request(**payload, response_processor=dummy_processor)
        prepared = req.prepare()
        assert not (prepared.get("json") is not None and prepared.get("data") is not None)
        assert prepared.get(payload_type) == {"some": "thing"}

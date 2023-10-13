from typing import Any

import pytest
import yarl
from pydantic import ValidationError

from reqme.request import Method
from reqme.request.schema import GenericSchema


@pytest.fixture
def payload() -> dict[str, Any]:
    return {
        "description": "Some description",
        "url": "https://www.somehost.com/somepath",
        "method": "POST",
        "headers": {"x-csrf-token": "blablablaba="},
        "body": {"heyjude": "dontmakemecry", "lalala": 123},
        "query_params": {"someparam": "1", "otherparam": "2"},
    }


class TestGenericSchema:
    def test_validate_url(self, payload):
        params = GenericSchema(**payload)
        assert isinstance(params.url, yarl.URL)
        assert params.url.is_absolute()
        assert str(params.url) == "https://www.somehost.com/somepath"

        """payload["url"] = "some-non-absolute-url/blabla"
        with pytest.raises(ValidationError):
            GenericSchema(**payload)"""

        payload["url"] = 123
        with pytest.raises(ValidationError):
            GenericSchema(**payload)

        del payload["url"]
        with pytest.raises(ValidationError):
            GenericSchema(**payload)

    def test_validate_method(self, payload):
        params = GenericSchema(**payload)
        assert isinstance(params.method, Method)
        assert params.method.value == "post"

        payload["method"] = "blablablo"
        with pytest.raises(ValidationError):
            GenericSchema(**payload)

        del payload["method"]
        with pytest.raises(ValidationError):
            GenericSchema(**payload)

    """def test_validate_body_formdata(self, payload):
        payload["form_data"] = {"this": "shouldn't be here"}
        with pytest.raises(ValueError):
            GenericSchema(**payload)
        del payload["body"]
        assert GenericSchema(**payload).form_data == {"this": "shouldn't be here"}"""

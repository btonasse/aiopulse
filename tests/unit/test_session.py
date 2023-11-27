import pytest

from aiopulse import Request, Session


class TestSession:
    @pytest.mark.parametrize(
        "body_or_form, payload_type",
        [
            ("body", "json"),
            ("form", "data"),
        ],
    )
    def test_prepare_request(self, dummy_request: Request, body_or_form, payload_type):
        # What a ridiculous way to parametrize a test! You really need to learn to pytest!
        session = Session()
        if body_or_form == "body":
            dummy_request.body = {"some": "thing"}
        elif body_or_form == "form":
            dummy_request.form_data = {"some": "thing"}
        req = session._prepare_request(dummy_request)
        assert req.get(payload_type) is not None
        assert req.get(payload_type) == {"some": "thing"}

    # Todo how to test the rest of this class? What a nightmare!

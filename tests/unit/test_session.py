import pytest

from aiopulse import Request, Session


class TestSession:
    @pytest.mark.parametrize(
        "dummy_request, payload_type",
        [
            ({"body": {"some": "thing"}}, "json"),
            ({"form_data": {"some": "thing"}}, "data"),
        ],
        indirect=["dummy_request"],
    )
    def test_prepare_request(self, dummy_request: Request, payload_type):
        session = Session()
        req = session._prepare_request(dummy_request)
        assert req.get(payload_type) is not None
        assert req.get(payload_type) == {"some": "thing"}

import pytest
from aiohttp import ClientResponse

from aiopulse.response import simple_json_processor


@pytest.fixture
def parametrized_response(request, dummy_response) -> ClientResponse:
    resp = {"some_stuff": 123}
    if request.param.get("list_resp"):
        dummy_response.json.return_value = [resp]
    else:
        dummy_response.json.return_value = resp
    dummy_response.status = request.param.get("status")
    dummy_response.reason = request.param.get("reason")
    return dummy_response


@pytest.mark.parametrize(
    "parametrized_response, error",
    [
        ({"status": 200, "list_resp": True}, None),
        ({"status": 399, "list_resp": True}, None),
        ({"status": 200, "list_resp": False}, None),
        ({"status": 400, "reason": "Bad request"}, "Bad request"),
        ({"status": 500, "reason": "Internal Error"}, "Internal Error"),
        ({"status": 200, "list_resp": True, "chain": True}, None),
    ],
    indirect=["parametrized_response"],
)
async def test_simple_json_processor(parametrized_response, error):
    processed = await simple_json_processor(parametrized_response)
    assert processed.error == error
    assert isinstance(processed.content, list)

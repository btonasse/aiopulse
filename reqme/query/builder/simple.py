from typing import Any

from query import Method
from yarl import URL

from . import RequestParams, RequestParamsBuilder


class SimpleBuilder(RequestParamsBuilder):
    @classmethod
    def parse_params(cls, data: dict[str, Any]) -> RequestParams:
        url: str = data["url"]
        method: Method = data["method"]

        return RequestParams(
            URL(url),
            method,
            data.get("payload", {}),
            data.get("headers", {}),
            data.get("form_data", {}),
            data.get("query_params", {}),
        )

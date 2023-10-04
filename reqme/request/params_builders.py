from typing import Any

from . import RequestParams


def simple_builder(data: dict[str, Any]) -> RequestParams:
    return RequestParams(
        url=data.get("url", None),
        method=data.get("method", None),
        body=data.get("body", {}),
        headers=data.get("headers", {}),
        form_data=data.get("form_data", {}),
        query_params=data.get("query_params", {}),
    )

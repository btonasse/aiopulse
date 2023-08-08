from typing import Any

import aiohttp
from custom_types import Method

from .builder import RequestParamsBuilder
from .processing import ProcessedResponse, ResponseProcessor


class Query:
    def __init__(self, raw_params: dict[str, Any], params_builder: RequestParamsBuilder, response_processor: ResponseProcessor) -> None:
        self._params = params_builder.parse_params(raw_params)
        self._processor = response_processor

    @property
    def url(self) -> str:
        return str(self._params.url)

    @property
    def method(self) -> Method:
        return self._params.method

    @property
    def payload(self) -> dict[str, Any]:
        return self._params.payload

    @property
    def headers(self) -> dict[str, str]:
        return self._params.headers

    @property
    def form_data(self) -> dict[str, Any]:
        return self._params.form_data

    @property
    def query_params(self) -> dict[str, str]:
        return self._params.query_params

    def process_response(self, response: aiohttp.ClientResponse) -> ProcessedResponse:
        return self._processor.process_response(response)

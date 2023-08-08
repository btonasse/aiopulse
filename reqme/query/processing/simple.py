import aiohttp
from query import Query

from . import ProcessedResponse, ResponseProcessor


class SimpleResponseProcessor(ResponseProcessor):
    @classmethod
    def process_response(cls, response: aiohttp.ClientResponse) -> ProcessedResponse:
        raise NotImplementedError

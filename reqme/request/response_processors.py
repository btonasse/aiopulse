from typing import Awaitable

import aiohttp

from . import ProcessedResponse


async def simple_processor(response: aiohttp.ClientResponse) -> Awaitable[ProcessedResponse]:
    raise NotImplementedError

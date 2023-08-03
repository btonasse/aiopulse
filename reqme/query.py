from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ProcessedResponse:
    ok: bool
    content: dict[str, Any]
    error: str
    query: Query
    next_query: Query | None = None


class Query:
    pass

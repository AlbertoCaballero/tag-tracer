"""
Data models for TagTracer.
"""

from pydantic import BaseModel


class NetworkRequest(BaseModel):
    """
    A normalized representation of a captured network request.
    """

    url: str
    method: str
    headers: dict[str, str] = {}
    post_data: str | None = None

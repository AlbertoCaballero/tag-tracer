"""
Data models for TagTracer.
"""
from pydantic import BaseModel
from typing import Dict, Optional

class NetworkRequest(BaseModel):
    """
    A normalized representation of a captured network request.
    """
    url: str
    method: str
    headers: Dict
    post_data: Optional[str] = None

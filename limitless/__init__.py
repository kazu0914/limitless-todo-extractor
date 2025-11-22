"""
Limitless Developer API クライアント

使用例:
    from limitless import LimitlessClient

    client = LimitlessClient()
    lifelogs = client.list_lifelogs(limit=10)
"""

from .client import LimitlessClient

__version__ = "1.0.0"
__all__ = ["LimitlessClient"]

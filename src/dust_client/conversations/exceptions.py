# dust_client/conversations/exceptions.py

from __future__ import annotations

from ..exceptions import DustError


class ConversationError(DustError):
    """
    Raised when a conversation-related operation (create, get, send message)
    fails due to invalid payloads, unexpected API response shapes,
    or Pydantic validation errors.
    """

    pass

# dust_client/chat/exceptions.py

from __future__ import annotations

from ..exceptions import DustError


class ChatError(DustError):
    """
    High-level errors raised by ChatClient when something goes wrong while
    streaming / aggregating the assistant's reply.
    """
    pass
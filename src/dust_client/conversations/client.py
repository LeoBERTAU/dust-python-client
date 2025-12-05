# dust_sdk/conversations/client.py

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from pydantic import ValidationError

from .exceptions import ConversationError
from .models import (
    Conversation,
    ConversationResponse,
    CreateMessagePayload,
    Message,
    MessageContext,
    MessageMention,
    MessageResponse,
)

if TYPE_CHECKING:
    from ..client import DustClient


class ConversationsClient:
    """
    Low-level client for the Assistant Conversations API.

    Accessed via `DustClient.conversations`.

    This layer is intentionally close to the HTTP API:
    - It exposes typed models for conversations & messages.
    - It does *not* stream events yet (that will be a higher-level abstraction).
    """

    def __init__(self, client: "DustClient") -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Conversations
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        title: Optional[str] = None,
        model: Optional[str] = None,
        blocking: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        POST /api/v1/w/{wId}/assistant/conversations

        Args:
            title: Optional human-readable title for the conversation.
            model: Optional model identifier (e.g. "claude-3-5-sonnet-20240620").
            blocking: Whether the API should block until the initial message is
                processed (if you also send one in extra payload).
                For now we default to True for simpler non-streaming use.
            extra: Optional additional fields to merge into the request body.

        Returns:
            Conversation: The created conversation.
        """
        body: Dict[str, Any] = {}

        if title is not None:
            body["title"] = title
        if model is not None:
            body["model"] = model
        body["blocking"] = blocking

        if extra:
            body.update(extra)

        data = self._client.workspace_request(
            "POST",
            "/assistant/conversations",
            json=body,
        )

        # Typical shape: { "conversation": { ... } }
        try:
            env = ConversationResponse.model_validate(data)
        except ValidationError as exc:
            raise ConversationError(
                f"Failed to parse conversation response: {exc}"
            ) from exc

        return env.conversation

    def get(self, conversation_id: str) -> Conversation:
        """
        Get an existing conversation.

        GET /api/v1/w/{wId}/assistant/conversations/{cId}

        Args:
            conversation_id: Conversation sId.

        Returns:
            Conversation
        """
        data = self._client.workspace_request(
            "GET",
            f"/assistant/conversations/{conversation_id}",
        )

        # Normal case: { "conversation": { ... } }
        if isinstance(data, dict) and "conversation" in data:
            try:
                env = ConversationResponse.model_validate(data)
                return env.conversation
            except ValidationError as exc:
                raise ConversationError(
                    f"Failed to parse conversation response: {exc}"
                ) from exc

        # Fallback: bare conversation object
        try:
            return Conversation.model_validate(data)
        except ValidationError as exc:
            raise ConversationError(
                f"Failed to parse conversation object: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def create_message(
        self,
        conversation_id: str,
        *,
        content: str,
        mentions: Sequence[MessageMention],
        context: Optional[MessageContext] = None,
        blocking: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Create a message in a conversation.

        POST /api/v1/w/{wId}/assistant/conversations/{cId}/messages

        Args:
            conversation_id: Conversation sId.
            content: Text content of the message (user query, etc.).
            mentions: Which agent configuration(s) should handle this message.
            context: Optional top-level context (timezone, username, etc.).
            blocking: Whether to block until the assistant has processed the
                message (non-streaming). For streaming we will expose a
                separate API later.
            extra: Optional additional fields to merge into the request body.

        Returns:
            Message: The created message (user message).
        """
        payload = CreateMessagePayload(
            content=content,
            mentions=list(mentions),
            context=context,
            blocking=blocking,
        )

        body = payload.model_dump(exclude_none=True)
        if extra:
            body.update(extra)

        data = self._client.workspace_request(
            "POST",
            f"/assistant/conversations/{conversation_id}/messages",
            json=body,
        )

        # Typical shape: { "message": { ... } }
        try:
            env = MessageResponse.model_validate(data)
        except ValidationError as exc:
            raise ConversationError(
                f"Failed to parse message response: {exc}"
            ) from exc

        return env.message
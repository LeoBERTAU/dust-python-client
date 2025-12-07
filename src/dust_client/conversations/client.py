# dust_client/conversations/client.py

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, TYPE_CHECKING, Iterator

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
    CancelMessagesPayload,
    CancelMessagesResponse,
    ConversationEvent,
    ConversationEventEnvelope,
)
from ..utils import stream_sse_json

if TYPE_CHECKING:
    from ..client import DustClient


class ConversationsClient:
    """
    Low-level client for the Assistant Conversations API.

    Accessed via `DustClient.conversations`.

    This layer is intentionally close to the HTTP API:
    - It exposes typed models for conversations & messages.
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
        blocking: bool = True,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        POST /api/v1/w/{wId}/assistant/conversations

        Args:
            title: Optional human-readable title for the conversation.
            blocking: Whether the API should block when an initial message
                is included in the payload (if you ever use that).
                For a plain empty conversation it's mostly a no-op but
                still accepted by the API.
            extra: Optional additional fields to merge into the request body.

        Returns:
            Conversation: The created conversation.
        """
        body: Dict[str, Any] = {}

        if title is not None:
            body["title"] = title

        # The docs mention `blocking` for event streaming behaviour.
        body["blocking"] = blocking

        if extra:
            body.update(extra)

        data = self._client.workspace_request(
            "POST",
            "/assistant/conversations",
            json=body,
        )

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
            extra: Optional additional fields to merge into the request body.

        Returns:
            Message: The created message (user message).
        """
        payload = CreateMessagePayload(
            content=content,
            mentions=list(mentions),
            context=context,
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
            raise ConversationError(f"Failed to parse message response: {exc}") from exc

        return env.message

    def edit_message(
        self,
        conversation_id: str,
        message_id: str,
        *,
        content: Optional[str] = None,
        mentions: Sequence[MessageMention],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Message:
        """
        Edit an existing message in a conversation.

        POST /api/v1/w/{wId}/assistant/conversations/{cId}/messages/{mId}/edit

        Dust's docs describe this endpoint as allowing you to change the content
        (and potentially mentions / context) and re-run the agent.

        Args:
            conversation_id: Conversation sId (cId).
            message_id: Message sId (mId) to edit.
            content: New text content for the message (optional, but usually provided).
            mentions: List of new mentions (agent configurations).
            extra: Optional additional fields to merge into the request body.

        Returns:
            Message: The updated message as returned by the API.
        """
        body: Dict[str, Any] = {}
        if content is not None:
            body["content"] = content
        body["mentions"] = [m.model_dump(exclude_none=True) for m in mentions]
        if extra:
            body.update(extra)

        data = self._client.workspace_request(
            "POST",
            f"/assistant/conversations/{conversation_id}/messages/{message_id}/edit",
            json=body,
        )

        # Most Dust endpoints wrap messages as { "message": { ... } }
        try:
            env = MessageResponse.model_validate(data)
            return env.message
        except ValidationError:
            # Fallback: try to parse a bare message object
            try:
                return Message.model_validate(data)
            except ValidationError as exc:
                raise ConversationError(
                    f"Failed to parse edited message response: {exc}"
                ) from exc

    def cancel_messages(
        self,
        conversation_id: str,
        message_ids: Sequence[str],
        extra: Optional[Dict[str, Any]] = None,
    ) -> CancelMessagesResponse:
        """
        Cancel the generation of one or more messages in a conversation.

        POST /api/v1/w/{wId}/assistant/conversations/{cId}/cancel
        """
        payload = CancelMessagesPayload(messageIds=list(message_ids))
        body = payload.model_dump(exclude_none=True)
        if extra:
            body.update(extra)

        data = self._client.workspace_request(
            "POST",
            f"/assistant/conversations/{conversation_id}/cancel",
            json=body,
        )

        try:
            return CancelMessagesResponse.model_validate(data)
        except ValidationError as exc:
            raise ConversationError(
                f"Failed to parse cancel response: {exc}; raw={data!r}"
            ) from exc

    # ------------------------------------------------------------------
    # Streaming events
    # ------------------------------------------------------------------

    def stream_events(
        self,
        conversation_id: str,
        *,
        timeout: Optional[float] = None,
    ) -> Iterator[ConversationEvent]:
        """
        Stream *conversation* events.

        GET /api/v1/w/{wId}/assistant/conversations/{cId}/events

        Yields:
            ConversationEvent: Parsed event objects from the SSE envelope.
        """
        effective_timeout = timeout or self._client.config.timeout

        path = (
            f"/api/v1/w/{self._client.config.workspace_id}"
            f"/assistant/conversations/{conversation_id}/events"
        )

        for raw in stream_sse_json(
            http=self._client.http,
            method="GET",
            path=path,
            timeout=effective_timeout,
        ):
            try:
                # Dust sends: { "eventId": "...", "data": { ... } }
                if isinstance(raw, dict) and "data" in raw:
                    env = ConversationEventEnvelope.model_validate(raw)
                    event = env.data
                else:
                    # Fallback: in case Dust ever sends bare event objects
                    event = ConversationEvent.model_validate(raw)
            except ValidationError as exc:
                raise ConversationError(
                    f"Failed to parse conversation event: {exc}; raw={raw!r}"
                ) from exc

            yield event

    def stream_message_events(
        self,
        conversation_id: str,
        message_id: str,
        *,
        timeout: Optional[float] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Stream *message* events for a specific message.

        GET /api/v1/w/{wId}/assistant/conversations/{cId}/messages/{mId}/events

        This is also a streaming endpoint (SSE / NDJSON). This generator
        yields each JSON event dict as it arrives.

        Example:
            from .models import ConversationEventType

            for event in client.conversations.stream_message_events(conv_id, msg_id):
                if event.get("type") == ConversationEventType.GENERATION_TOKENS:
                    ...
        """
        effective_timeout = timeout or self._client.config.timeout

        path = (
            f"/api/v1/w/{self._client.config.workspace_id}"
            f"/assistant/conversations/{conversation_id}/messages/{message_id}/events"
        )

        yield from stream_sse_json(
            http=self._client.http,
            method="GET",
            path=path,
            timeout=effective_timeout,
        )

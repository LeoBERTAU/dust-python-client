# dust_client/conversations/models.py

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict


class Conversation(BaseModel):
    """
    Minimal representation of a Dust conversation.

    Based on:
    {
      "conversation": {
        "sId": "DhvpbhW74S",
        "title": "Systems Thinking Conversation",
        "created_at": 1742923287427,
        ...
      }
    }
    """

    model_config = ConfigDict(extra="allow")

    sId: str = Field(..., description="Stable identifier for the conversation.")
    title: Optional[str] = Field(
        default=None,
        description="Human-readable title of the conversation.",
    )
    created_at: Optional[int] = Field(
        default=None,
        description="Creation timestamp in milliseconds since epoch.",
    )


class ConversationResponse(BaseModel):
    """
    Envelope used by the API for conversation responses:

    {
      "conversation": { ... }
    }
    """

    model_config = ConfigDict(extra="allow")

    conversation: Conversation


class ConversationEventType(str, Enum):
    USER_MESSAGE_NEW = "user_message_new"
    USER_MESSAGE_EDIT = "user_message_edit"

    AGENT_MESSAGE_NEW = "agent_message_new"
    AGENT_MESSAGE_PROGRESS = "agent_message_progress"  # optional depending on workspace
    AGENT_MESSAGE_DONE = "agent_message_done"
    AGENT_ERROR = "agent_error"

    GENERATION_TOKENS = "generation_tokens"  # streaming tokens (agent output)


class ConversationEvent(BaseModel):
    """
    A single conversation event, from the `data` field of the SSE payload.

    The raw SSE event looks like:
    {
      "eventId": "...",
      "data": {
        "type": "user_message_new",
        "created": 1765043283715,
        "messageId": "p7accylgUm",
        "message": { ... }
      }
    }
    """

    model_config = ConfigDict(extra="allow")

    type: ConversationEventType = Field(
        ...,
        description=(
            "Event type (e.g. user_message_new, agent_message_new, "
            "agent_message_done, generation_tokens, agent_error)."
        ),
    )
    created: Optional[int] = Field(
        default=None,
        description="Event creation timestamp (ms since epoch).",
    )
    messageId: Optional[str] = Field(
        default=None,
        description="Related message sId, if any.",
    )
    # `message` uses the existing Message model; extra fields are allowed.
    message: Optional[Message] = None


class ConversationEventEnvelope(BaseModel):
    """
    Envelope for SSE conversation events.

    Shape:

    {
      "eventId": "1765043283716-0",
      "data": { ... ConversationEvent ... }
    }
    """

    model_config = ConfigDict(extra="allow")

    eventId: str
    data: ConversationEvent


class ConversationEventsResponse(BaseModel):
    """
    Envelope for conversation or message events:

        {
          "events": [ { ... }, ... ]
        }

    We expose raw ConversationEvent objects and allow extra fields.
    """

    model_config = ConfigDict(extra="allow")

    events: List[ConversationEvent]


# ---------------------------------------------------------------------------
# Message-related models
# ---------------------------------------------------------------------------


class MessageMentionContext(BaseModel):
    """
    Context attached to a mention.

    Example from MCP server:

    "context": {
      "timezone": "Europe/Berlin",
      "modelSettings": {"provider": "anthropic"}
    }
    """

    model_config = ConfigDict(extra="allow")

    timezone: Optional[str] = None
    modelSettings: Optional[Dict[str, Any]] = None


class MessageMention(BaseModel):
    """
    A mention tells Dust which agent configuration(s) should handle the message.

    Example:
    {
      "configurationId": "{AGENT_ID}",
      "context": {
        "timezone": "Europe/Berlin",
        "modelSettings": {"provider": "anthropic"}
      }
    }
    """

    model_config = ConfigDict(extra="allow")

    configurationId: str
    context: Optional[MessageMentionContext] = None


class MessageContext(BaseModel):
    """
    Top-level context for the message.

    Example from MCP server retrieval:

    "context": {
      "timezone": "Europe/Berlin",
      "username": "api_retrieval",
      "queryType": "history_analysis"
    }
    """

    model_config = ConfigDict(extra="allow")

    timezone: Optional[str] = None
    username: Optional[str] = None
    queryType: Optional[str] = None


class CreateMessagePayload(BaseModel):
    """
    Request payload for POST /assistant/conversations/{cId}/messages

    Minimal typical shape:

    {
      "content": "Explain the MCP Protocol in detail",
      "mentions": [
        {
          "configurationId": "{AGENT_ID}",
          "context": { ... }
        }
      ],
      "context": { ... },
      "blocking": true
    }
    """

    model_config = ConfigDict(extra="allow")

    content: str
    mentions: List[MessageMention]
    context: Optional[MessageContext] = None


class CancelMessagesPayload(BaseModel):
    """
    Request payload for POST
      /assistant/conversations/{cId}/cancel

    The endpoint accepts MULTIPLE message IDs.
    """

    model_config = ConfigDict(extra="allow")

    messageIds: List[str]


class CancelMessagesResponse(BaseModel):
    """
    Minimal typed response for the cancel endpoint.

    Dust currently returns something like:

        { "success": true }

    We allow extra keys to remain forward-compatible.
    """

    model_config = ConfigDict(extra="allow")

    success: bool = Field(..., description="Whether the cancel operation succeeded.")


class Message(BaseModel):
    """
    Minimal representation of a message returned by the API.

    Example:

    {
      "message": {
        "sId": "qwenj3rusI",
        "conversation_sId": "DhvpbhW74S",
        "content": "Explain the MCP Protocol in detail",
        "author_name": "User",
        "author_type": "user",
        "created_at": 1742923287627
      }
    }
    """

    model_config = ConfigDict(extra="allow")

    sId: str
    conversation_sId: Optional[str] = None
    content: Optional[str] = None
    author_name: Optional[str] = None
    author_type: Optional[str] = None
    created_at: Optional[int] = None


class MessageResponse(BaseModel):
    """
    Envelope used by the API for message creation responses:

    {
      "message": { ... }
    }
    """

    model_config = ConfigDict(extra="allow")

    message: Message

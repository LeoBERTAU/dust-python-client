# dust_sdk/conversations/models.py

from __future__ import annotations

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
    blocking: Optional[bool] = None


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

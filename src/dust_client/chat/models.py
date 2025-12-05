# dust_sdk/chat/models.py

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


class ChatMessage(BaseModel):
    """
    High-level representation of a chat message, as seen by ChatClient users.

    This wraps the lower-level Conversations `Message` model and simplifies it
    to a role + text abstraction while still exposing IDs for debugging.
    """

    model_config = ConfigDict(extra="allow")

    role: Literal["user", "assistant"] = Field(
        ..., description="Role of the message author in the chat."
    )
    text: str = Field(..., description="Message text content.")
    message_id: str = Field(..., description="Underlying Dust message sId.")
    conversation_id: str = Field(..., description="Conversation sId this message belongs to.")


class ChatResponse(BaseModel):
    """
    Response returned by ChatClient when using blocking (non-streaming) calls.

    For now, we reliably expose the user message and conversation_id.
    The assistant_message field is reserved for future use, once we wire
    conversation events / agent message aggregation.
    """

    model_config = ConfigDict(extra="allow")

    conversation_id: str = Field(
        ..., description="Conversation sId used for this interaction."
    )
    user_message: ChatMessage = Field(
        ..., description="The user message that was just sent."
    )
    assistant_message: Optional[ChatMessage] = Field(
        default=None,
        description=(
            "The assistant's reply, if available. Currently None until we hook "
            "into conversation events / agent messages."
        ),
    )
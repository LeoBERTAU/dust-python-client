# tests/test_chat_client.py

from __future__ import annotations

from typing import Iterator
from types import SimpleNamespace

import pytest

from dust_client.chat.models import ChatResponse
from dust_client.conversations.models import (
    Conversation,
    Message,
    MessageMention,
    MessageContext,
    ConversationEvent,
    ConversationEventType,
)


def _fake_conversation() -> Conversation:
    return Conversation(sId="conv123", title="Test conv")


def _fake_user_message() -> Message:
    return Message(
        sId="msg_user_1",
        conversation_sId="conv123",
        content="Hello from ChatClient!",
        author_name="User",
        author_type="user",
    )


def _fake_event_stream(user_msg_id: str) -> Iterator[ConversationEvent]:
    """
    Simulate the minimal sequence of events needed by ChatClient._wait_for_assistant_reply:

      1) agent_message_new  -> to discover the agent message id via parentMessageId
      2) agent_message_done -> to know the reply is finished
    """
    # Fake agent message with a parentMessageId pointing to the user message
    agent_msg = Message(
        sId="msg_agent_1",
        conversation_sId="conv123",
        content=None,
        author_name="Assistant",
        author_type="assistant",
    )
    # extra="allow" on Message means we can attach extra attributes
    setattr(agent_msg, "parentMessageId", user_msg_id)

    yield ConversationEvent(
        type=ConversationEventType.AGENT_MESSAGE_NEW,
        created=123,
        messageId=None,
        message=agent_msg,
    )

    yield ConversationEvent(
        type=ConversationEventType.AGENT_MESSAGE_DONE,
        created=124,
        messageId=agent_msg.sId,
        message=None,
    )


def test_chat_send_creates_conv_and_aggregates_reply(chat_client, monkeypatch):
    """
    High-level test:
      - ChatClient.send() should:
        * create a conversation when conversation_id=None
        * create a user message
        * stream events
        * re-fetch conversation and extract the agent reply
        * return a ChatResponse with assistant_message.text == "Hello world!"
    """

    conv = _fake_conversation()
    user_msg = _fake_user_message()

    # 1) Patch ConversationsClient.create to return our fake conversation
    def fake_create(title=None, blocking=True, extra=None):
        return conv

    # 2) Patch ConversationsClient.create_message to return our fake user message
    def fake_create_message(conversation_id, content, mentions, context, extra=None):
        assert conversation_id == conv.sId
        assert content == "Hello from ChatClient!"
        assert isinstance(mentions[0], MessageMention)
        assert isinstance(context, MessageContext)
        return user_msg

    # 3) Patch ConversationsClient.stream_events to yield fake ConversationEvent objects
    def fake_stream_events(conversation_id: str, timeout=None):
        assert conversation_id == conv.sId
        # NOTE: _fake_event_stream returns an *iterator*, so we just return it
        return _fake_event_stream(user_msg.sId)

    # 4) Patch ConversationsClient.get to return a conversation whose content
    #    includes the final agent message text.
    #
    # ChatClient._wait_for_assistant_reply will look at conv.content, which in
    # the real API is a 2D list of message dicts. We'll mimic just enough of
    # that structure for the code to find the agent_message with the right sId.
    def fake_get(conversation_id: str):
        assert conversation_id == conv.sId

        conv_content = [
            [
                {
                    "id": 1,
                    "sId": user_msg.sId,
                    "type": "user_message",
                    "content": user_msg.content,
                },
                {
                    "id": 2,
                    "sId": "msg_agent_1",
                    "type": "agent_message",
                    "content": "Hello world!",
                },
            ]
        ]

        # We don't need a full Conversation model here; ChatClient only cares
        # about `.content` and maybe `.sId`, so a SimpleNamespace is enough.
        return SimpleNamespace(sId=conv.sId, title=conv.title, content=conv_content)

    # Wire these patches into the ChatClient's conversations instance
    monkeypatch.setattr(chat_client._conversations, "create", fake_create)
    monkeypatch.setattr(
        chat_client._conversations, "create_message", fake_create_message
    )
    monkeypatch.setattr(chat_client._conversations, "stream_events", fake_stream_events)
    monkeypatch.setattr(chat_client._conversations, "get", fake_get)

    # Now call ChatClient.send
    resp: ChatResponse = chat_client.send(
        agent="helper",
        text="Hello from ChatClient!",
        username="leo",
        timezone="Europe/Paris",
        conversation_id=None,
        title="ChatClient demo",
    )

    assert resp.conversation_id == conv.sId
    assert resp.user_message.text == "Hello from ChatClient!"
    assert resp.user_message.message_id == user_msg.sId

    assert resp.assistant_message is not None
    assert resp.assistant_message.text == "Hello world!"
    assert resp.assistant_message.message_id == "msg_agent_1"


def test_chat_send_requires_username(chat_client, monkeypatch):
    """
    username is required; ChatClient should raise DustError.

    We stub ConversationsClient.create so no real HTTP (or DummyDustClient stub failure)
    occurs before the username validation kicks in.
    """
    from dust_client.exceptions import DustError

    # Return a minimal conversation object when create() is called.
    conv_stub = SimpleNamespace(sId="conv_stub")

    monkeypatch.setattr(
        chat_client._conversations,
        "create",
        lambda title=None, blocking=True, extra=None: conv_stub,
    )

    with pytest.raises(DustError):
        chat_client.send(
            agent="helper",
            text="Hi",
            username="",  # invalid
        )

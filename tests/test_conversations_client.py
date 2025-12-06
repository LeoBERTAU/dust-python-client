# tests/test_conversations_client.py

from __future__ import annotations

from dust_client.conversations.models import (
    Conversation,
    Message,
    MessageMention,
    MessageMentionContext,
    MessageContext,
)


def test_create_conversation_builds_correct_request(dummy_dust_client, conversations_client):
    dummy_dust_client.set_response(
        "POST",
        "/assistant/conversations",
        {
            "conversation": {
                "sId": "abc123",
                "title": "SDK test",
            }
        },
    )

    conv = conversations_client.create(title="SDK test", blocking=True)

    # Response parsed correctly
    assert isinstance(conv, Conversation)
    assert conv.sId == "abc123"
    assert conv.title == "SDK test"

    # Request shape correct
    assert len(dummy_dust_client.calls) == 1
    call = dummy_dust_client.calls[0]
    assert call["method"] == "POST"
    assert call["path"] == "/assistant/conversations"
    # blocking + title should both be present
    assert call["json"]["title"] == "SDK test"
    assert call["json"]["blocking"] is True


def test_create_message_builds_payload_and_parses_response(dummy_dust_client, conversations_client):
    conv_id = "conv123"
    path = f"/assistant/conversations/{conv_id}/messages"

    dummy_dust_client.set_response(
        "POST",
        path,
        {
            "message": {
                "sId": "msg123",
                "conversation_sId": conv_id,
                "content": "Hello!",
                "author_name": "User",
                "author_type": "user",
            }
        },
    )

    mention_ctx = MessageMentionContext(timezone="Europe/Paris")
    mention = MessageMention(configurationId="helper", context=mention_ctx)
    ctx = MessageContext(timezone="Europe/Paris", username="leo")

    msg = conversations_client.create_message(
        conv_id,
        content="Hello!",
        mentions=[mention],
        context=ctx,
    )

    # Parsed
    assert isinstance(msg, Message)
    assert msg.sId == "msg123"
    assert msg.conversation_sId == conv_id
    assert msg.content == "Hello!"
    assert msg.author_type == "user"

    # Request payload
    assert len(dummy_dust_client.calls) == 1
    call = dummy_dust_client.calls[0]
    assert call["method"] == "POST"
    assert call["path"] == path
    body = call["json"]
    assert body["content"] == "Hello!"
    assert body["context"]["username"] == "leo"
    assert body["mentions"][0]["configurationId"] == "helper"
    assert body["mentions"][0]["context"]["timezone"] == "Europe/Paris"


def test_cancel_messages_parses_success(dummy_dust_client, conversations_client):
    conv_id = "conv123"
    path = f"/assistant/conversations/{conv_id}/cancel"

    dummy_dust_client.set_response(
        "POST",
        path,
        {"success": True},
    )

    resp = conversations_client.cancel_messages(conv_id, ["m1", "m2"])
    assert resp.success is True

    call = dummy_dust_client.calls[0]
    assert call["path"] == path
    assert call["json"]["messageIds"] == ["m1", "m2"]
# Conversations Examples

This page provides practical examples of working with conversations and messages in Dust using the Python SDK.

---

## Create a Conversation

```python
from dust_client import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)

conversation = client.conversations.create(
    title="SDK Test Conversation"
)

print("Conversation created:", conversation.sId)
```

---

## Send a Message to an Agent (Blocking)

```python
from dust_client.conversations.models import (
    MessageMention,
    MessageMentionContext,
    MessageContext,
)

agent_id = "your-agent-sid"

mention = MessageMention(
    configurationId=agent_id,
    context=MessageMentionContext(timezone="Europe/Paris"),
)

msg_context = MessageContext(
    username="SDKUser",
    timezone="Europe/Paris",
)

message = client.conversations.create_message(
    conv_id=conversation.sId,
    content="Hello from the Dust Python SDK!",
    mentions=[mention],
    context=msg_context,
    blocking=True,
)

print("Assistant replied:", message.content)
```

---

## List Messages in a Conversation

```python
messages = client.conversations.list_messages(conversation.sId)

for m in messages:
    print(m.author_name, ":", m.content)
```

---

## Fetch a Single Message

```python
message = client.conversations.get_message(
    conv_id=conversation.sId,
    message_id="your-message-sid"
)

print(message.author_name, message.content)
```

---

## Delete a Message

```python
client.conversations.delete_message(
    conv_id=conversation.sId,
    message_id="your-message-sid",
)

print("Message deleted.")
```

---

## Error Handling Example

```python
from dust_client.exceptions import DustAPIError

try:
    client.conversations.get_message("bad-conv-id", "bad-msg-id")
except DustAPIError as e:
    print("Error:", e)
    print("Details:", e.details)
```

---

## Tip: Use the ChatClient for Simpler Interaction

```python
response = client.chat.send(
    agent="your-agent-sid",
    message="Summarize the README of the Dust Python Client."
)

print("Response:", response.text)
```


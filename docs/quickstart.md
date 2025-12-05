# Quickstart

Welcome to the **Dust Python Client**!  
This guide shows how to authenticate, list agents, create a conversation, and send your first message.

---

## 1. Install the SDK

If you cloned the repository:

```bash
pip install -e ".[dev]"
```

Once published to PyPI:
```bash
pip install dust-client
```

---

## 2. Set Up Credentials

Export your Dust credentials:
```bash
export DUST_WORKSPACE_ID="your-workspace-id"
export DUST_API_KEY="your-api-key"
```
Or create a .env file:
```code
DUST_WORKSPACE_ID=your-workspace-id
DUST_API_KEY=your-api-key
```

---

## 3. Initialize the Client

```python
from dust_client import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)

client.validate()
print("Authenticated!")
```

---

## 4. List Agents

```python
agents = client.agents.list()

for a in agents:
    print(a.sId, "-", a.name)
```

---

## 5. Create a Conversation

```python
conv = client.conversations.create(title="My First Conversation")
print("Conversation created:", conv.sId)
```

---

## 6. Send a Message to an Agent

```python
from dust_client.conversations.models import MessageMention, MessageMentionContext, MessageContext

agent_id = "your-agent-sid"

mention = MessageMention(
    configurationId=agent_id,
    context=MessageMentionContext(timezone="Europe/Paris")
)

ctx = MessageContext(username="SDKUser", timezone="Europe/Paris")

msg = client.conversations.create_message(
    conv_id=conv.sId,
    content="Hello from the Python SDK!",
    mentions=[mention],
    context=ctx,
    blocking=True,
)

print("Agent replied:", msg.content)
```

---

## 7. Recommended: Use the ChatClient for Simpler Interaction

Send a blocking message in one line:

```python
response = client.chat.send(
    agent="your-agent-sid",
    message="Give me a summary of the Dust Python Client repo."
)

print("Assistant:", response.text)
```

---

## You’re Ready to Build 🚀

You now know how to:
- Authenticate
- Work with agents
- Create conversations
- Send messages and get responses

Next steps:
- Explore the full API: agents, conversations, messages
- Build wrappers for your applications
- Automate workflows using Dust agents





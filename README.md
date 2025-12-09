
# Dust Client for Python (Unofficial)

[![PyPI version](https://img.shields.io/pypi/v/dust-client.svg)](https://pypi.org/project/dust-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/dust-client.svg)](https://pypi.org/project/dust-client/)
[![CI](https://github.com/LeoBERTAU/dust-python-client/actions/workflows/ci.yml/badge.svg)](https://github.com/LeoBERTAU/dust-python-client/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python client for the [Dust Developer Platform](https://dust.tt).  
This SDK provides Python-friendly access to Dust’s **Agents**, **Conversations**, and (eventually) other API endpoints.

The goal is to offer a clean, typed, modern interface similar to the official JavaScript SDK — but fully native for Python developers.

> ⚠️ **Status: Early development (alpha)**  
> Only a subset of APIs are implemented so far.  
> The API surface may change until v1.0.

---

## ✨ Features

### ✅ Implemented

- **Configuration & auth**
  - Workspace-scoped `DustConfig` (Pydantic)
  - API key / access token authentication
  - `DustConfig.from_env()` for `DUST_WORKSPACE_ID` / `DUST_API_KEY`

- **Core client**
  - `DustClient` with shared HTTP wiring (via `httpx`)
  - `workspace_request(...)` helper for `/api/v1/w/{wId}/...`
  - Centralized error handling:
    - `DustError`, `DustAPIError`
    - HTTP-specific subclasses like `DustBadRequestError`, `DustUnauthorizedError`, etc.

- **Agents API** (`DustClient.agents`)
  - `list()` – list agent configurations
  - `get(sid)` – fetch a single agent by its `sId`
  - `search(q=...)` – search agents by name
  - `create(...)` – create a new agent configuration
  - `update(sid, ...)` – update an existing agent configuration
  - `delete(sid)` – delete an agent configuration
  - Typed models with Pydantic (e.g. `AgentConfiguration`, `ListAgentsResponse`)

- **Conversations API** (`DustClient.conversations`)
  - `create(title=...)` – create a conversation
  - `create_message(...)` – send messages into a conversation
  - Typed models:
    - `Conversation`
    - `Message`
    - `MessageContext`, `MessageMention`, `MessageMentionContext`
  - Basic blocking workflow: send a message mentioning an agent and wait for processing

- **High-level Chat API** (`DustClient.chat`)
  - Opinionated, ergonomic wrapper on top of Conversations:
    - `ChatClient.send(...)` – one-shot call:
      - creates a conversation if needed
      - sends a user message
      - uses `blocking=True` under the hood
    - `ChatClient.session(...)` – stateful session with:
      - bound `agent` (agent configuration `sId`)
      - `username`
      - optional `timezone`
      - persistent `conversation_id`
    - `ChatSession.send(...)` – send multiple messages in the same conversation
  - High-level models:
    - `ChatMessage`
    - `ChatResponse`

> Note: in the current alpha, `ChatResponse.assistant_message` is reserved for future use.  
> We first expose the user message and conversation ID reliably; assistant aggregation will be added once events are wired.

### 🔧 In progress

- Conversation events / agent messages:
  - Expose conversation / message events in a typed way
  - Aggregate the final assistant reply for blocking mode
  - Add streaming support on top of events

### 🗺️ Upcoming (roadmap)

- Datasources & Documents API
- Datasource Views
- Workspace Search
- Apps & Runs API
- Tools (MCP) integration
- Triggers
- Pagination helpers
- Async client (`AsyncDustClient`)
- Full documentation site (mkdocs)

---

## 📦 Installation

### Development (recommended for now)

Clone the repository and install in editable mode:

```bash
git clone https://github.com/LeoBERTAU/dust-python-client.git
cd dust-python-client
pip install -e ".[dev]"
```

This installs the `dust_client` package plus dev tools (`pytest`, `ruff`, `python-dotenv`).

### (Future) Installation from PyPI

```bash
pip install dust-client
```

Not available yet — will be published once the API stabilizes.

---

## 🔑 Authentication Guide

To use the Dust Python SDK, you need two pieces of information:

1. **Workspace ID** (`wId`)
2. **API Key**

Both are obtained from the Dust web application.

### 1. Finding Your Workspace ID (`wId`)

Your workspace ID is visible directly in the URL when you browse your workspace.

Navigate to any workspace page (e.g., Workspace Settings, API Keys, People & Security) and look at the URL. It will look like:

> `https://eu.dust.tt/w/<WORKSPACE_ID>/workspace`

The `<WORKSPACE_ID>` segment is what you should pass to `DustConfig`.

### 2. Creating or Retrieving an API Key

Dust API Keys are managed inside your workspace under **Admin → API Keys**.

Steps:

1. Log into Dust at <https://dust.tt> (or your regional URL).
2. In the left sidebar, click **Admin**.
3. Under **Builder Tools**, select **API Keys**.
4. Click **Create API Key** in the top-right corner.
5. Give the key a name (e.g., `SDK Development`).
6. Copy the generated API key — you will not be able to view it again.

If a key is lost, revoke it and create a new one.

### 3. Using Your Credentials in Python

#### Option A — Explicit configuration

```python
from dust_client import DustClient, DustConfig

config = DustConfig(
    workspace_id="YOUR_WORKSPACE_ID_HERE",
    api_key="YOUR_API_KEY_HERE",
)

client = DustClient(config)
client.validate()  # optional, checks workspace & token
```

#### Option B — Using environment variables

```bash
export DUST_WORKSPACE_ID=YOUR_WORKSPACE_ID
export DUST_API_KEY=YOUR_API_KEY
```

```python
from dust_client import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)
```

#### Credentials you should **not** use

- Browser session tokens → ❌ unsupported
- Slack/Teams bot tokens → ❌ not API keys
- Workspace Secrets (Admin → Secrets) → ❌ not for authentication
- OAuth tokens → ✔️ supported only when obtained through Dust OAuth flows

For most SDK use cases, a **Workspace API Key** is the recommended method.

---

## 🚀 Quickstart

### 1. Create and validate a client

```python
from dotenv import load_dotenv
from dust_client import DustClient, DustConfig

load_dotenv()  # loads DUST_WORKSPACE_ID / DUST_API_KEY if present

config = DustConfig.from_env()
client = DustClient(config)

# Optional: perform a lightweight API check
client.validate()
```

### 2. List agents

```python
from dust_client import DustAPIError

try:
    agents = client.agents.list()
    print(f"Found {len(agents)} agents")
    for a in agents:
        print("-", a.name or a.sId, f"(sId={a.sId})")
except DustAPIError as e:
    print("Dust API error:", e)
    if e.details:
        print("Details:", e.details)
```

### 3. One-shot chat with an agent (`ChatClient.send`)

```python
resp = client.chat.send(
    agent="dust",               # agent configuration sId (e.g. "dust" or "i5cIwRsG0u")
    text="Hello from the Python SDK!",
    username="your-username",   # logical username in your workspace
    timezone="Europe/Paris",
)

print("Conversation ID:", resp.conversation_id)
print("User said:", resp.user_message.text)
print("Assistant:", resp.assistant_message)  # currently None until events are wired
```

### 4. Stateful session (`ChatClient.session`)

```python
session = client.chat.session(
    agent="dust",
    username="your-username",
    timezone="Europe/Paris",
    title="SDK test conversation",
)

resp1 = session.send("Help me design a Python SDK for Dust.")
print("User:", resp1.user_message.text)

resp2 = session.send("Generate a README section about conversations.")
print("User:", resp2.user_message.text)
```

Under the hood, all messages stay in the same conversation (`session.conversation_id`).

---

## 🧩 API Overview

### Core types

- `DustConfig` – holds base URL, workspace ID, API key/access token, timeout, etc.
- `DustClient` – main entrypoint.
- Sub-clients:
  - `client.agents` – agents-related operations
  - `client.conversations` – low-level conversations & messages
  - `client.chat` – high-level chat abstraction

### Exceptions

All SDK-specific errors inherit from `DustError`.  
HTTP-level errors are `DustAPIError` or its subclasses:

- `DustBadRequestError` (400)
- `DustUnauthorizedError` (401)
- `DustForbiddenError` (403)
- `DustNotFoundError` (404)
- `DustConflictError` (409)
- `DustRateLimitError` (429)
- `DustServerError` (5xx)

You can either catch `DustError` broadly or specific subclasses for finer control.

---

## 🧠 Agents API

The Agents API is exposed via `client.agents`.

### List agents

```python
agents = client.agents.list()
for a in agents:
    print(a.sId, a.name)
```

### Get a single agent

```python
agent = client.agents.get("i5cIwRsG0u")
print(agent.sId, agent.name, agent.description)
```

### Search agents by name

```python
results = client.agents.search(q="promptWriter")
for a in results:
    print(a.sId, a.name)
```

### Create / update / delete (shape may evolve)

```python
# Create
created = client.agents.create(
    name="My new agent",
    description="Created from the Python SDK",
    # plus other fields matching the Dust API
)

# Update
updated = client.agents.update(
    created.sId,
    description="Updated description from the SDK",
)

# Delete
client.agents.delete(created.sId)
```

Refer to the official Dust docs for the full JSON shape of agent configurations.

---

## 💬 Conversations & Messages (low-level)

The Conversations API is exposed via `client.conversations`.  
This gives you full control over conversation lifecycles and message payloads.

For a deeper explanation of the conversation model and the roles of:

- `Message`
- `MessageContext`
- `MessageMention`
- `MessageMentionContext`

see: [`docs/conversations.md`](docs/examples/conversations.md)

### Basic example

```python
from dust_client.conversations.models import (
    MessageContext,
    MessageMention,
    MessageMentionContext,
)

# 1) Create a conversation
conv = client.conversations.create(title="SDK test conversation")
print("Conversation:", conv.sId, conv.title)

# 2) Prepare context & mention
ctx = MessageContext(
    username="your-username",
    timezone="Europe/Paris",
)

mention_ctx = MessageMentionContext(
    timezone="Europe/Paris",
)

mention = MessageMention(
    configurationId="dust",  # agent configuration sId
    context=mention_ctx,
)

# 3) Send a message (blocking)
msg = client.conversations.create_message(
    conversation_id=conv.sId,
    content="Hello from the low-level Conversations API!",
    mentions=[mention],
    context=ctx,
    blocking=True,
)

print("Message sId:", msg.sId)
```

---

## 💬 High-level Chat API

For most applications, the high-level `ChatClient` (`client.chat`) is easier to use than the raw Conversations API.

- Takes care of:
  - Creating conversations (if needed)
  - Building `MessageContext` and `MessageMention`
  - Using `blocking=True` by default

Use `client.chat.send(...)` for one-shot calls, or `client.chat.session(...)` for long-running conversations.

See the **Quickstart** section above for examples.

---

## 📁 Examples

The repo includes a few example scripts in the `examples/` folder:

- `examples/agents.py`
  - List agents, get an agent, search by name.
- `examples/conversations.py`
  - Create a conversation and send a message with an agent mention.

You can run them with:

```bash
python examples/agents.py
python examples/conversations.py
```

Make sure your `.env` or environment variables provide `DUST_WORKSPACE_ID` and `DUST_API_KEY`.

---

## 🛠 Development

Install in editable mode with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run linting (Ruff):

```bash
ruff check .
```

---

## 📜 License

This project is licensed under the **MIT License**.  
See [`LICENSE`](LICENSE) for details.

---

## 🙋‍♂️ Notes

- This is an **unofficial** SDK, built by the community.
- Always refer to the official Dust documentation for the most accurate and up-to-date API reference: <https://docs.dust.tt>
- Feedback, issues, and PRs are very welcome at: <https://github.com/LeoBERTAU/dust-python-client>


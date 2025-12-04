# Dust SDK for Python (Unofficial)

**A Python client for the Dust Developer Platform (https://dust.tt).**  
This SDK provides Python-friendly access to Dust’s Agents, Conversations, Datasources, and other API endpoints.

The goal is to offer a clean, typed, modern interface similar to the official JavaScript SDK — but fully native for Python developers.

> ⚠️ **Status:** Early development (alpha).  
> Only a subset of APIs are implemented so far.  
> The API surface may change until v1.0.

---

## ✨ Features (current & planned)

### ✔️ Implemented (Phase 1 & 2)
- Workspace authentication (API key or access token)
- Fully typed `DustConfig` using Pydantic
- Centralized error handling with `DustError` & `DustAPIError`
- Core HTTP client (`DustClient`)
- Basic Agents API:
  - `list_agents()` returning typed `AgentConfiguration`

### 🚧 In progress
- Conversations:
  - Create conversation
  - Add messages
  - Retrieve conversation state
  - **Streaming agent responses** (async generator)
- More typing & models using Pydantic

### 📅 Upcoming
- Datasources & Documents API
- Datasource Views
- Workspace Search
- Apps & Runs API
- Tools (MCP) integration
- Triggers
- Pagination helpers
- Async client (`AsyncDustClient`)
- CLI utility (`dust-cli`)
- Full documentation site (mkdocs)

---

## 📦 Installation

### Development (recommended for contributors)

```
git clone https://github.com/<yourname>/dust-sdk.git
cd dust-sdk
pip install -e .
```

### (Future) Installation from PyPI
```
pip install dust-sdk
```
*Not available yet — will be published once we reach a stable alpha.*

## 🔑 Authentication Guide

To use the Dust Python SDK, you need **two pieces of information**:

1. **Workspace ID (`wId`)**
2. **API Key**

Both are obtained from the Dust web application.

---

### 1. Finding Your Workspace ID (wId)

Your workspace ID is visible directly in the URL when you browse your workspace.

Navigate to any workspace page (e.g., *Workspace Settings*, *API Keys*, *People & Security*) and look at the URL. It will look like:

> https://eu.dust.tt/w/<WORKSPACE_ID>/workspace

This value is required for all API endpoints.

---

### 2. Creating or Retrieving an API Key

Dust API Keys are managed inside your workspace under **Admin → API Keys**.

Follow these steps:

1. Log into Dust at https://dust.tt (or your regional URL).
2. In the left sidebar, click **Admin**.
3. Under **Builder Tools**, select **API Keys**.
4. Click **Create API Key** in the top-right corner.
5. Give the key a name (e.g., *SDK Development*).
6. Copy the generated API key — **you will not be able to view it again**.

If a key is lost, revoke it and create a new one.

---

### 3. Using Your Credentials in Python

#### Option A — Explicit configuration

```python
from dust_sdk import DustClient, DustConfig

config = DustConfig(
    workspace_id="YOUR_WORKSPACE_ID_HERE",
    api_key="YOUR_API_KEY_HERE",
)

client = DustClient(config)
```

#### Option B — Using environment variables

```
export DUST_WORKSPACE_ID=h9p9uyOJxmD
export DUST_API_KEY=YOUR_API_KEY_HERE
```

```python
from dust_sdk import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)
```
---

### Credentials You Should Not Use

- Browser session tokens → ❌ unsupported
- Slack/Teams bot tokens → ❌ not API keys
- Workspace Secrets (Admin → Secrets) → ❌ not for authentication
- OAuth tokens → ✔️ supported only when obtained through Dust OAuth flows

For most SDK use cases, a Workspace API Key is the recommended method.


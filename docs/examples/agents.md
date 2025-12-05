# Agents Examples

This page shows practical examples of how to interact with Dust agents using the `AgentsClient`.

---

## List All Agents

```python
from dust_client import DustClient, DustConfig

config = DustConfig.from_env()
client = DustClient(config)

agents = client.agents.list()

print(f"Found {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} (sId={agent.sId})")
```

---

## Get a Single Agent

```python
agent = client.agents.get("your-agent-sid")
print(agent.name, agent.description)
```

---

## Search for an Agent by Name

```python
results = client.agents.search(q="writer")

for agent in results:
    print(agent.sId, agent.name)
```

---

## Create a New Agent

```python
new_agent = client.agents.create(
    name="DemoAgent",
    description="Agent created through Python SDK",
    instructions="Respond politely and concisely.",
    model={
        "providerId": "openai",
        "modelId": "gpt-4o-mini",
        "temperature": 0.4,
    },
)

print("Created agent:", new_agent.sId)
```

---

## Update an Existing Agent

```python
updated = client.agents.update(
    "your-agent-sid",
    name="Updated Name",
    description="Updated description",
)

print("Updated:", updated.sId)
```

---

## Error Handling Example

```python
from dust_client.exceptions import DustAPIError

try:
    agent = client.agents.get("invalid-id")
except DustAPIError as e:
    print("API Error:", e)
    print("Details:", e.details)
```

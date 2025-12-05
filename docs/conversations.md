# Dust SDK – Conversation Model Overview

This document explains the **core objects used when interacting with Dust conversations**, based on the Dust Conversation API.  
It is intended for SDK contributors and advanced users who want to understand how messages, contexts, and agent mentions fit together.

---

# 🚀 Overview

Dust’s conversation system is centered around **messages**, but each message can involve:

- **user metadata** (who is speaking)
- **multiple agents** reacting to the same message
- **optional per-agent overrides**
- **execution metadata** when messages trigger agent runs

To support this, the Dust API exposes four key object types:

1. **Message**
2. **MessageContext**
3. **MessageMention**
4. **MessageMentionContext**

Understanding these objects makes the whole API intuitive.

---

# 1. `Message`  
Represents a single message inside a conversation.

A message includes:

- **content** — the text written by the user or an agent
- **author metadata**
- **context** — user environment info
- **mentions** — which agents were invoked by this message
- **run info** — only when agents execute

### Example
```json
{
  "sId": "msg_123",
  "content": "Hello!",
  "author": "user",
  "context": { "username": "leo", "timezone": "Europe/Paris" },
  "mentions": [ {...}, {...} ]
}
```

A **Message** is the *final object* Dust stores inside the conversation timeline.

---

# 2. `MessageContext`  
Metadata about the **user sending the message**.

This context describes *how* the message should be interpreted, not what it contains.

It can include:

- `username`
- `timezone`
- `locale`
- (other metadata may exist depending on the workspace configuration)

### Example
```json
{
  "username": "leo",
  "timezone": "Europe/Paris"
}
```

### Purpose
Dust uses this for:

- running date‑aware operations  
- identifying message ownership  
- tailoring formatting or responses  

> **MessageContext = metadata describing the sender environment.**

---

# 3. `MessageMention`  
Specifies **which agent(s)** should respond to a message.

A single user message can trigger **multiple agents**.

Fields:

- `configurationId` — the agent SID
- `context` — optional per‑agent overrides (e.g., timezone)
- `run_id` — added by the API when the agent executes

### Example
```json
{
  "configurationId": "agent_sId_ABC",
  "context": {
    "timezone": "Europe/Paris"
  }
}
```

### Purpose
> **A MessageMention is “please run agent X on this message.”**

You can send a single message and trigger multiple agents in parallel.

---

# 4. `MessageMentionContext`  
Optional context applied **only to a specific agent during its execution**.

It overrides global MessageContext fields *only for that agent*.

### Example
```json
{
  "timezone": "Europe/Paris"
}
```

### When to use it
- different agents require different locales  
- different reasoning context per agent  
- advanced multi-agent workflows  

> **MessageMentionContext = agent‑specific execution metadata.**

---

# 🧠 Visual Model

```
Message
 ├── content: "Hello agent!"
 ├── context (MessageContext)
 │     ├─ username = "leo"
 │     └─ timezone = "Europe/Paris"
 └── mentions (list of MessageMention)
        ├─ mention 1 → agent A (MessageMentionContext)
        └─ mention 2 → agent B (MessageMentionContext)
```

---

# 🗂 Summary Table

| Object | What It Represents | When You Use It |
|--------|--------------------|------------------|
| **Message** | The actual message in the conversation | Always |
| **MessageContext** | User metadata (username, timezone, locale) | Always when sending messages |
| **MessageMention** | Which agent should process the message | When invoking agents |
| **MessageMentionContext** | Overrides for one specific agent | Optional, advanced use cases |

---

# 💡 Why Dust Uses This Structure

Because Dust supports:

- multi-agent routing  
- per-agent custom contexts  
- toolsets and agent-specific behaviors  
- timezone‑aware reasoning  
- enterprise workflows with auditing  

This is much more flexible than a typical chat API, and the SDK mirrors that clean layering.

---

# ✅ Conclusion

You now understand:

- **what each message object does**
- **how conversations work under the hood**
- **how agents are invoked inside a conversation**

This knowledge is essential for implementing:

✔ `ConversationClient`  
✔ `ChatClient` (high-level chat interface)  
✔ Future support for streaming, events, and agent routing  

Feel free to extend this file as the SDK evolves.

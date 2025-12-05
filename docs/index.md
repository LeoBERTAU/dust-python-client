# Dust Python Client

Unofficial Python SDK for the [Dust Developer Platform](https://dust.tt).

This library provides a modern, typed, Pythonic interface on top of Dust’s HTTP APIs:

- Agents
- Conversations & messages
- High-level chat helpers

The goal is to mirror the spirit of the official JavaScript SDK, but tailored to Python:

- `httpx` for HTTP
- `pydantic` for typed models
- Clear, modular sub-clients (`agents`, `conversations`, `chat`)

> ⚠️ **Status: Alpha**
>
> Only a subset of APIs are implemented.  
> Expect some breaking changes before `1.0.0`.

---

## What’s Included

- ✅ `DustConfig` and `DustClient`
- ✅ API-key authentication & workspace scoping
- ✅ Agents API (`client.agents`)
- ✅ Conversations API (`client.conversations`)
- ✅ High-level Chat API (`client.chat`)
- ✅ Centralized error handling (`DustError`, `DustAPIError`, HTTP-specific subclasses)

See:

- [Installation](installation.md)
- [Quickstart](quickstart.md)
- [Usage Overview](usage.md)
- [Examples](examples/agents.md)
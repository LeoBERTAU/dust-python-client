# tests/conftest.py

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from dust_client.config import DustConfig
from dust_client.conversations.client import ConversationsClient
from dust_client.chat.client import ChatClient


class DummyDustClient:
    """
    Minimal fake DustClient used for unit tests.

    - Records workspace_request calls
    - Allows you to pre-configure return values
    """

    def __init__(self, config: DustConfig) -> None:
        self.config = config
        self.calls: List[Dict[str, Any]] = []
        # Optional: map (method, path) -> return value
        self._responses: Dict[tuple[str, str], Any] = {}
        # `http` needed by stream_sse_json, but unit tests will usually monkeypatch that.
        self.http = None

    def set_response(self, method: str, path: str, response: Any) -> None:
        self._responses[(method.upper(), path)] = response

    def workspace_request(
        self,
        method: str,
        path: str,
        json: Dict[str, Any] | None = None,
    ) -> Any:
        method = method.upper()
        self.calls.append({"method": method, "path": path, "json": json})
        key = (method, path)
        if key not in self._responses:
            raise RuntimeError(f"No stubbed response for {method} {path}")
        return self._responses[key]


@pytest.fixture
def dummy_config() -> DustConfig:
    # Values don't matter, we never hit the real API.
    return DustConfig(
        base_url="https://example.test",
        workspace_id="w_test",
        api_key="dummy",
        timeout=5.0,
    )


@pytest.fixture
def dummy_dust_client(dummy_config: DustConfig) -> DummyDustClient:
    return DummyDustClient(dummy_config)


@pytest.fixture
def conversations_client(dummy_dust_client: DummyDustClient) -> ConversationsClient:
    return ConversationsClient(client=dummy_dust_client)


@pytest.fixture
def chat_client(conversations_client: ConversationsClient, dummy_config: DustConfig) -> ChatClient:
    # AgentsClient isn’t used by ChatClient right now; pass None / dummy.
    class DummyAgentsClient:
        pass

    return ChatClient(
        conversations=conversations_client,
        agents=DummyAgentsClient(),  # type: ignore[arg-type]
        config=dummy_config,
    )
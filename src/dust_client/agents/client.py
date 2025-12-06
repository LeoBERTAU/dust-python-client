# dust_client/agents/client.py
from __future__ import annotations

from typing import TYPE_CHECKING, Literal, List

from pydantic import ValidationError

from ..exceptions import DustError
from .models import AgentConfiguration, ListAgentsResponse, GetAgentResponse

if TYPE_CHECKING:
    from ..client import DustClient


class AgentsClient:
    """
    Client for Dust Agent-related operations.

    Accessed via `DustClient.agents`.
    """

    def __init__(self, client: "DustClient") -> None:
        self._client = client

    # ------------------------------------------------------------------
    # List agents
    # ------------------------------------------------------------------

    def list(self) -> List[AgentConfiguration]:
        """
        List agent configurations for the workspace.

        GET /api/v1/w/{wId}/assistant/agent_configurations
        """
        data = self._client.workspace_request(
            "GET",
            "/assistant/agent_configurations",
        )

        # Happy path: Dust returns the documented shape
        if isinstance(data, dict) and "agentConfigurations" in data:
            resp = ListAgentsResponse.model_validate(data)
            return resp.agentConfigurations

        # Fallbacks for robustness (in case Dust changes or tests mock differently)
        if isinstance(data, list):
            # API returned a bare list of agents
            return [AgentConfiguration.model_validate(a) for a in data]

        if isinstance(data, dict):
            # Try a few other common wrapper keys
            for key in ("agents", "agent_configurations", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return [AgentConfiguration.model_validate(a) for a in value]

        raise DustError(
            f"Unexpected response type for AgentsClient.list: {type(data)!r}"
        )

    # ------------------------------------------------------------------
    # Get a single agent by sId
    # ------------------------------------------------------------------

    def get(
        self,
        s_id: str,
        *,
        variant: Literal["light", "full"] = "light",
    ) -> AgentConfiguration:
        """
        Retrieve a single agent configuration by its stable ID (`sId`).

        Maps to:
            GET /api/v1/w/{wId}/assistant/agent_configurations/{sId}

        Args:
            s_id: The agent configuration stable ID (e.g. "dust", "helper", "i5cIwRsG0u").
            variant: "light" for basic data (default), "full" for full tools/actions config.

        Returns:
            AgentConfiguration
        """
        params = {"variant": variant} if variant else None

        data = self._client.workspace_request(
            "GET",
            f"/assistant/agent_configurations/{s_id}",
            params=params,
        )

        try:
            resp = GetAgentResponse.model_validate(data)
        except ValidationError as e:
            raise DustError(
                f"Failed to parse get agent response: {e}"
            ) from e

        return resp.agentConfiguration

    # ------------------------------------------------------------------
    # Update (favorite flag only – public API limitation)
    # ------------------------------------------------------------------

    def update(
        self,
        s_id: str,
        *,
        user_favorite: bool,
    ) -> AgentConfiguration:
        """
        Update an agent configuration.

        **Public API limitation:** currently only `userFavorite` is supported,
        i.e. you can mark/unmark an agent as a favorite for the authenticated user.

        Maps to:
            PATCH /api/v1/w/{wId}/assistant/agent_configurations/{sId}

        Args:
            s_id: Agent configuration stable ID.
            user_favorite: Whether this agent should be marked as favorite.

        Returns:
            Updated AgentConfiguration
        """
        payload = {"userFavorite": user_favorite}

        data = self._client.workspace_request(
            "PATCH",
            f"/assistant/agent_configurations/{s_id}",
            json=payload,
        )

        try:
            resp = GetAgentResponse.model_validate(data)
        except ValidationError as e:
            raise DustError(
                f"Failed to parse update agent response: {e}"
            ) from e

        return resp.agentConfiguration

    # ------------------------------------------------------------------
    # Search by name
    # ------------------------------------------------------------------

    def search(self, q: str) -> List[AgentConfiguration]:
        """
        Search agent configurations by name.

        Maps to:
            GET /api/v1/w/{wId}/assistant/agent_configurations/search?q=...

        Args:
            q: Full or partial name to search for.

        Returns:
            List[AgentConfiguration]
        """
        data = self._client.workspace_request(
            "GET",
            "/assistant/agent_configurations/search",
            params={"q": q},
        )

        try:
            resp = ListAgentsResponse.model_validate(data)
        except ValidationError as e:
            raise DustError(
                f"Failed to parse search agents response: {e}"
            ) from e

        return resp.agentConfigurations

    # ------------------------------------------------------------------
    # Unsupported operations (create/delete)
    # ------------------------------------------------------------------

    def create(self, *args, **kwargs) -> AgentConfiguration:  # type: ignore[override]
        """
        Creating agent configurations is not supported by the public Dust API.

        Agents are currently created/edited via the Dust UI or other internal tooling.
        This method exists only for API completeness and will always raise.
        """
        raise DustError(
            "AgentsClient.create is not supported: "
            "the public Dust API does not expose an agent creation endpoint."
        )

    def delete(self, s_id: str) -> None:
        """
        Deleting agent configurations is not supported by the public Dust API.

        This method exists only for API completeness and will always raise.
        """
        raise DustError(
            "AgentsClient.delete is not supported: "
            "the public Dust API does not expose an agent deletion endpoint."
        )
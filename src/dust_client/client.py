# dust_client/client.py

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from .config import DustConfig
from .agents.client import AgentsClient
from .conversations.client import ConversationsClient
from .chat.client import ChatClient
from .exceptions import (
    DustError,
    map_status_to_error,
)

__all__ = ["DustClient"]


class DustClient:
    """
    Synchronous Dust API client.

    Example:
        from dust_client import DustClient, DustConfig

        config = DustConfig(
            workspace_id="YOUR_WORKSPACE_ID",
            api_key="YOUR_API_KEY_OR_ACCESS_TOKEN",
        )
        client = DustClient(config)

        agents = client.list_agents()
    """

    def __init__(
            self,
            config: DustConfig,
            *,
            client: Optional[httpx.Client] = None,
            user_agent_suffix: Optional[str] = None,
            validate_on_init: bool = False,
    ) -> None:
        self._config = config

        token = config.api_key or config.access_token
        assert token, "DustConfig should guarantee that a token is present."

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": self._build_user_agent(user_agent_suffix),
        }

        self._client = client or httpx.Client(
            base_url=str(config.base_url),
            timeout=config.timeout,
            headers=headers,
        )

        # Set sub clients
        self.agents = AgentsClient(
            client=self,
        )
        self.conversations = ConversationsClient(
            client=self,
        )
        self.chat = ChatClient(
            conversations=self.conversations,
            agents=self.agents,
            config=self._config,
        )

        if validate_on_init:
            # Raises DustError / DustAPIError if invalid
            self.validate()

    @property
    def config(self) -> DustConfig:
        return self._config

    @property
    def http(self) -> httpx.Client:
        """Expose the underlying httpx client (read-only) for advanced use."""
        return self._client

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def _build_user_agent(self, suffix: Optional[str]) -> str:
        base = "dust-sdk-py/0.1.0"
        if suffix:
            return f"{base} {suffix}"
        return base

    # ------------------------------------------------------------------
    # Core request method
    # ------------------------------------------------------------------

    def request(
            self,
            method: str,
            path: str,
            *,
            params: Optional[Dict[str, Any]] = None,
            json: Optional[Dict[str, Any]] = None,
            parse_json: bool = True,
    ) -> Any:
        """
        Internal helper to call the Dust HTTP API.

        Raises:
            DustError       on network issues or JSON parsing issues.
            DustAPIError    (or subclass) on non-2xx HTTP responses.

        If `parse_json` is False, returns the raw httpx.Response on success.
        """
        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
            )
        except httpx.HTTPError as exc:
            # network / connection / timeout errors
            raise DustError(f"Network error while calling Dust API: {exc}") from exc

        status = response.status_code

        # ------------------------------------------------------------------
        # Success path
        # ------------------------------------------------------------------
        if 200 <= status < 300:
            if not parse_json:
                return response

            if not response.content:
                return None

            try:
                return response.json()
            except ValueError as exc:
                raise DustError(
                    f"Failed to parse JSON response from Dust API: {exc}"
                ) from exc

        # ------------------------------------------------------------------
        # Error path (non-2xx)
        # ------------------------------------------------------------------
        try:
            payload = response.json()
        except ValueError:
            # Not JSON, fall back to plain text
            ErrorClass = map_status_to_error(status)
            raise ErrorClass(
                status_code=status,
                message=response.text or "Unknown error",
                details={"raw": response.text},
            )

        code: Optional[str] = None
        message: str = "Unknown error"
        details: Dict[str, Any] = {}

        if isinstance(payload, dict):
            details = payload

            # Common Dust error shapes:
            # { "error": { "code": "...", "message": "...", ... } }
            if "error" in payload and isinstance(payload["error"], dict):
                err = payload["error"]
                code = err.get("code") or err.get("type") or None
                message = (
                        err.get("message")
                        or err.get("detail")
                        or err.get("error")
                        or message
                )
            else:
                # Or flat: { "code": "...", "message": "...", ... }
                code = payload.get("code") or payload.get("error")
                message = (
                        payload.get("message")
                        or payload.get("detail")
                        or payload.get("error_description")
                        or message
                )

        ErrorClass = map_status_to_error(status)
        raise ErrorClass(
            status_code=status,
            message=message,
            code=code,
            details=details,
        )

    def workspace_request(
        self,
        method: str,
        relative_path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        parse_json: bool = True,
    ) -> Any:
        """
        Helper for workspace-scoped endpoints.

        Builds a path like:
            /api/v1/w/{workspace_id}{relative_path}

        Example:
            _workspace_request("GET", "/assistant/agent_configurations")
            -> /api/v1/w/<wId>/assistant/agent_configurations
        """
        if not relative_path.startswith("/"):
            relative_path = "/" + relative_path

        path = f"/api/v1/w/{self._config.workspace_id}{relative_path}"
        return self.request(
            method=method,
            path=path,
            params=params,
            json=json,
            parse_json=parse_json,
        )


    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Validate the client configuration against the Dust API.

        This performs a lightweight request to confirm that the workspace ID
        and token are accepted by the API.

        On success, returns None.
        On failure, raises DustError or DustAPIError.
        """
        # We use the assistant/agent_configurations endpoint as a simple authenticated check:
        self.workspace_request(
            "GET",
            "/assistant/agent_configurations",
            parse_json=False,
        )

from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationError, model_validator


DEFAULT_DUST_BASE_URL = "https://dust.tt"


class DustConfig(BaseModel):
    """
    Configuration for DustClient.

    Typical usage:

        DustConfig(
            workspace_id="...",
            api_key="...",  # or access_token="..."
        )

    You can also load from environment via `from_env()`.
    """

    base_url: HttpUrl | str = Field(
        default=DEFAULT_DUST_BASE_URL,
        description="Base URL of the Dust API (usually https://dust.tt).",
    )
    workspace_id: str = Field(..., description="Dust workspace ID (wId).")
    api_key: Optional[str] = Field(
        default=None,
        description="Workspace API key, used as Bearer token.",
    )
    access_token: Optional[str] = Field(
        default=None,
        description="OAuth access token, alternative to api_key.",
    )
    timeout: float = Field(
        default=60.0,
        description="Default request timeout in seconds.",
    )

    @model_validator(mode="after")
    def _ensure_auth_present(self) -> "DustConfig":
        if not (self.api_key or self.access_token):
            raise ValueError("Either `api_key` or `access_token` must be provided.")
        return self

    @classmethod
    def from_env(cls, **overrides: object) -> "DustConfig":
        """
        Build config from environment variables:

        - DUST_BASE_URL (optional, default https://dust.tt)
        - DUST_WORKSPACE_ID (required)
        - DUST_API_KEY (optional)
        - DUST_ACCESS_TOKEN (optional)

        Explicit keyword arguments override env values.
        """
        base_url = overrides.get("base_url") or os.getenv(
            "DUST_BASE_URL",
            DEFAULT_DUST_BASE_URL,
        )
        workspace_id = overrides.get("workspace_id") or os.getenv("DUST_WORKSPACE_ID")
        api_key = overrides.get("api_key") or os.getenv("DUST_API_KEY")
        access_token = overrides.get("access_token") or os.getenv("DUST_ACCESS_TOKEN")
        timeout = float(overrides.get("timeout") or os.getenv("DUST_TIMEOUT", "60.0"))

        if not workspace_id:
            raise ValidationError.from_exception_data(
                title="DustConfig",
                line_errors=[
                    {
                        "type": "value_error.missing",
                        "loc": ("workspace_id",),
                        "msg": "workspace_id is required (env: DUST_WORKSPACE_ID)",
                        "input": None,
                    }
                ],
            )

        return cls(
            base_url=base_url,
            workspace_id=workspace_id,
            api_key=api_key,  # validator will enforce at least one of api_key/access_token
            access_token=access_token,
            timeout=timeout,
        )
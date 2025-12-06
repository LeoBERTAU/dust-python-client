# dust_client/agents/models.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class AgentModelConfig(BaseModel):
    """
    Model configuration for an Agent.

    Matches Dust's shape:

        {
          "providerId": "<string>",
          "modelId": "<string>",
          "temperature": "<number>"
        }

    Extra fields are allowed for forward compatibility
    (e.g. reasoningEffort, etc.).
    """

    model_config = ConfigDict(extra="allow")

    providerId: str = Field(..., description="LLM provider identifier (e.g. 'openai').")
    modelId: str = Field(..., description="Underlying model identifier (e.g. 'gpt-5').")
    temperature: float = Field(..., description="Sampling temperature for the model.")


class AgentConfiguration(BaseModel):
    """
        Representation of a Dust agent configuration.

    This mirrors the documented API payload shape of a single agent configuration
    and allows extra fields for forward compatibility.
    """

    model_config = ConfigDict(extra="allow")

    # Core identity and versioning
    id: int = Field(..., description="Internal numeric identifier.")
    sId: str = Field(..., description="Stable public string identifier (sId).")
    version: int = Field(..., description="Version number of this configuration.")
    versionCreatedAt: Optional[datetime] = Field(
        default=None,
        description="ISO timestamp of when this version was created.",
    )
    versionAuthorId: str | int | None = Field(
        default=None,
        description="Identifier of the author of this version (string or numeric).",
    )

    # Human-facing info
    name: str = Field(..., description="Human-readable agent name.")
    description: Optional[str] = Field(
        default=None,
        description="Optional description of the agent.",
    )
    instructions: Optional[str] = Field(
        default=None,
        description="System / prompt instructions for the agent.",
    )
    pictureUrl: Optional[HttpUrl] = Field(
        default=None,
        description="Avatar / picture URL for this agent.",
    )

    # Status and visibility
    status: str = Field(
        ...,
        description="Agent status (e.g. 'active').",
    )
    scope: str = Field(
        ...,
        description="Visibility scope (e.g. 'global', 'visible', ...).",
    )
    userFavorite: Optional[bool] = Field(
        default=None,
        description="User-specific Favorite status, if provided by the API.",
    )
    userListStatus: Optional[str] = Field(
        default=None,
        description="User-specific list status, if provided by the API.",
    )

    # Model config
    model: Optional[AgentModelConfig] = Field(
        default=None,
        description="Underlying model configuration for the agent.",
    )

    # Behavior / actions
    actions: List[Any] = Field(
        default_factory=list,
        description="List of actions/tools attached to the agent.",
    )
    maxStepsPerRun: Optional[int] = Field(
        default=None,
        description="Maximum number of steps per run, if configured.",
    )
    templateId: Optional[str] = Field(
        default=None,
        description="Associated template identifier, if any.",
    )


class ListAgentsResponse(BaseModel):
    """
    Response wrapper for list agents API.
    """
    agentConfigurations: List[AgentConfiguration]

class GetAgentResponse(BaseModel):
    """
    Response wrapper for get agents API.
    """
    agentConfiguration: AgentConfiguration


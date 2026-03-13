"""Frozen Pydantic models for typed payloads."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiscoveryRequest(BaseModel):
    """Root input: what token to discover."""

    model_config = ConfigDict(frozen=True)
    contract_address: str
    chain_name: str
    chain_id: int


class PipelineConfig(BaseModel):
    """Runtime configuration persisted as a root document."""

    model_config = ConfigDict(frozen=True)
    search_model: str
    formatting_model: str
    final_report_model: str
    lifi_base_url: str
    lifi_timeout_seconds: int
    search_context_size: Literal["low", "medium", "high"]


class TokenIdentity(BaseModel):
    """Token identity from Li.Fi /token endpoint."""

    model_config = ConfigDict(frozen=True)
    address: str
    chain_id: int
    coin_key: str | None
    name: str
    symbol: str
    decimals: int
    logo_uri: str = ""


class ChainInfo(BaseModel):
    """Single chain entry from Li.Fi /chains endpoint."""

    model_config = ConfigDict(frozen=True)
    id: int
    name: str
    key: str


class ChainMap(BaseModel):
    """Envelope for chain ID → name mapping."""

    model_config = ConfigDict(frozen=True)
    chains: list[ChainInfo]


class Deployment(BaseModel):
    """Single token deployment on a chain."""

    model_config = ConfigDict(frozen=True)
    chain_id: int
    chain_name: str
    address: str
    decimals: int
    source: str  # "lifi", "grok", "both"
    verification_status: Literal["official", "official_bridged", "verified", "unverified"] = "verified"
    source_urls: list[str] = Field(default_factory=list)
    verification_notes: str = ""


class ObservedDeployment(BaseModel):
    """Observed token deployment candidate gathered from web research or APIs."""

    model_config = ConfigDict(frozen=True)
    chain_name: str
    address: str
    chain_id: int | None = None
    source_urls: list[str] = Field(default_factory=list)
    evidence: str = ""
    confidence: Literal["confirmed", "likely", "uncertain"] = "uncertain"
    classification: Literal["official", "official_bridged", "third_party", "unknown"] = "unknown"


class DeploymentResearch(BaseModel):
    """Broad deployment observations gathered from search."""

    model_config = ConfigDict(frozen=True)
    observed_deployments: list[ObservedDeployment] = Field(default_factory=list)
    notes: str = ""


class DeploymentInventory(BaseModel):
    """All known deployments for a token."""

    model_config = ConfigDict(frozen=True)
    token_name: str
    token_symbol: str
    deployments: list[Deployment]
    observed_deployments: list[ObservedDeployment] = Field(default_factory=list)


class BridgeRoute(BaseModel):
    """Single bridge route between two deployments."""

    model_config = ConfigDict(frozen=True)
    from_chain_id: int
    from_chain_name: str
    to_chain_id: int
    to_chain_name: str
    bridge_name: str
    estimated_time_seconds: int = 0
    fee_usd: str = ""
    source: str  # "lifi", "grok", "both"


class BridgeProtocol(BaseModel):
    """Single bridge protocol and its known route coverage."""

    model_config = ConfigDict(frozen=True)
    name: str
    official_url: str = ""
    project_recommended: bool = False
    notes: str = ""
    routes: list[BridgeRoute] = Field(default_factory=list)


class BridgeInventory(BaseModel):
    """All known bridge protocols and routes for a token."""

    model_config = ConfigDict(frozen=True)
    token_name: str
    protocols: list[BridgeProtocol] = Field(default_factory=list)
    failed_route_pairs: list[str] = Field(default_factory=list)


class AuditScope(BaseModel):
    """Defines what a single audit search targets."""

    model_config = ConfigDict(frozen=True)
    scope_type: str  # "core", "chain", "bridge"
    scope_name: str  # e.g., "ethereum", "stargate", or "core"


class GrokDeploymentEntry(BaseModel):
    """Backward-compatible alias model for older notes and experiments."""

    model_config = ConfigDict(frozen=True)
    chain_name: str
    contract_address: str
    source_url: str = ""
    confidence: str = ""  # "confirmed", "likely", "uncertain"

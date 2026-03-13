"""All Document subclasses for the cross-chain token discovery pipeline."""

from ai_pipeline_core import Document

from .models import (
    BridgeInventory,
    ChainMap,
    DeploymentInventory,
    DeploymentResearch,
    DiscoveryRequest,
    PipelineConfig,
    TokenIdentity,
)


# --- Pipeline Input ---
class PipelineConfigDocument(Document[PipelineConfig]):
    """Root runtime configuration for the pipeline."""


class DiscoveryRequestDocument(Document[DiscoveryRequest]):
    """Root input: contract address + chain name."""


# --- Step 1: Deployments ---
class ChainMapDocument(Document[ChainMap]):
    """Li.Fi chain ID → name mapping."""


class TokenIdentityDocument(Document[TokenIdentity]):
    """Token identity from Li.Fi /token endpoint."""


class LifiDeploymentsDocument(Document):
    """Deployments found via Li.Fi token list filtered by coinKey (JSON)."""


class DeploymentResearchDocument(Document[DeploymentResearch]):
    """Web-searched deployment observations from Grok (JSON)."""


class DeploymentsDocument(Document[DeploymentInventory]):
    """Consolidated deployments from Li.Fi + Grok (JSON)."""

    publicly_visible = True


# --- Step 2: Bridges ---
class BridgeRoutesRawDocument(Document):
    """Raw Li.Fi bridge routes for one deployment pair (JSON)."""


class BridgeResearchDocument(Document):
    """Project bridge info from Grok web search (Markdown)."""


class BridgesDocument(Document[BridgeInventory]):
    """Consolidated bridge data from Li.Fi + Grok (JSON)."""

    publicly_visible = True


# --- Step 3: Transfer Instructions ---
class TransferInstructionsDocument(Document):
    """Step-by-step transfer instructions for one bridge protocol (Markdown)."""

    publicly_visible = True


# --- Step 4: Chain Assessments ---
class ChainAssessmentDocument(Document):
    """Security/maturity assessment for one chain (Markdown)."""

    publicly_visible = True


# --- Step 5: Audit Research ---
class AuditResearchDocument(Document):
    """Audit research results for one scope (Markdown)."""

    publicly_visible = True


# --- Step 6: Report ---
class IssuesFindingsDocument(Document):
    """Phase 1: comprehensive list of all issues and findings (Markdown)."""


class FilteredFindingsDocument(Document):
    """Phase 2: importance-ranked and filtered findings (Markdown)."""


class FinalReportDocument(Document):
    """Phase 3: final structured report (Markdown)."""

    publicly_visible = True

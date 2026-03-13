"""Prompt specs for Step 1: Token deployment discovery and consolidation."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import (
    ChainMapDocument,
    DeploymentResearchDocument,
    LifiDeploymentsDocument,
    TokenIdentityDocument,
)
from ..models import DeploymentInventory, DeploymentResearch
from .components import (
    BlockchainResearcher,
    CiteExactAddresses,
    CiteWebSources,
    NoInformationLoss,
    TechnicalDocumentWriter,
)


class DeploymentSearchSpec(PromptSpec[DeploymentResearch]):
    """Search broadly for token deployments and bridged representations."""

    role = BlockchainResearcher
    input_documents = (TokenIdentityDocument,)
    task = (
        "Search broadly for deployments or bridged representations of the token identified in context across every "
        "blockchain. Do not limit the search to canonical or native deployments, and do not discard a result only "
        "because its official status is unclear. Include official native deployments, officially supported bridged "
        "deployments or OFT-style representations, and other observed token addresses that are widely referenced. "
        "For each observed deployment, provide the exact address, source URLs, a short evidence summary, confidence, "
        "and classification. Prefer exact source pages from project docs, bridge docs, block explorers, or other "
        "reputable primary sources instead of homepages. Use 'official' for canonical/native deployments, "
        "'official_bridged' for officially supported bridged or omnichain representations, 'third_party' for "
        "non-official third-party representations, and 'unknown' when the status is unclear. If a chain ID is known "
        "from the source, include it."
    )
    rules = (CiteExactAddresses, CiteWebSources)

    token_name: str = Field(description="Token name (e.g., PancakeSwap)")
    token_symbol: str = Field(description="Token symbol (e.g., CAKE)")


class ConsolidateDeploymentsSpec(PromptSpec[DeploymentInventory]):
    """Merge Li.Fi and Grok deployment data into a single deduplicated inventory."""

    role = TechnicalDocumentWriter
    input_documents = (LifiDeploymentsDocument, DeploymentResearchDocument, ChainMapDocument)
    task = (
        "Merge the Li.Fi deployment data and the broad web-researched deployment observations into a single "
        "verified inventory. Return a DeploymentInventory object with token_name, token_symbol, deployments, and "
        "observed_deployments. The deployments list should contain addresses that are verified enough to use in "
        "downstream routing and chain analysis. Include canonical/native deployments and officially supported bridged "
        "deployments when there is enough evidence, and keep other discoveries in observed_deployments with their "
        "classification and evidence. For each verified deployment include chain_name, chain_id, address, decimals, "
        "source attribution, verification_status, source_urls, and verification_notes. Treat Li.Fi as strong but not "
        "exclusive evidence; use the web research source URLs and notes to verify, classify, or downgrade entries. "
        "Deduplicate by matching chain_id + address. Use the chain map to resolve chain IDs to human-readable names. "
        "Do not lose search findings just because they are not verified for routing."
    )
    rules = (NoInformationLoss, CiteExactAddresses)

    token_name: str = Field(description="Token name")
    token_symbol: str = Field(description="Token symbol")

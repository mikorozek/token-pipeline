"""Prompt specs for Step 2: Bridge route discovery and consolidation."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import (
    BridgeResearchDocument,
    BridgeRoutesRawDocument,
    ChainMapDocument,
    TokenIdentityDocument,
)
from ..models import BridgeInventory
from .components import (
    BlockchainResearcher,
    CiteExactAddresses,
    CiteWebSources,
    MarkdownOutput,
    NoInformationLoss,
    TechnicalDocumentWriter,
)


class BridgeSearchSpec(PromptSpec):
    """Search for project-specific bridge information not covered by Li.Fi."""

    role = BlockchainResearcher
    input_documents = (TokenIdentityDocument,)
    task = (
        "Search for the project's official bridging documentation, bridge partnerships, "
        "and any native bridge mechanisms for the token identified in context. "
        "Look for: native OFT bridges, project-run bridge UIs, partner bridges with reduced fees, "
        "and any official bridging recommendations from the project team. "
        "Extract bridge name, supported routes, official URL, and whether it is the project-recommended method."
    )
    rules = (CiteExactAddresses, CiteWebSources)
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Project Bridge Information\n\n"
        "## Official Recommendations\n\n"
        "## Notes"
    )

    token_name: str = Field(description="Token name")
    token_symbol: str = Field(description="Token symbol")


class ConsolidateBridgesSpec(PromptSpec[BridgeInventory]):
    """Merge Li.Fi route data and Grok bridge research into a single bridges document."""

    role = TechnicalDocumentWriter
    input_documents = (BridgeRoutesRawDocument, BridgeResearchDocument, ChainMapDocument)
    task = (
        "Consolidate all bridge route data from Li.Fi API responses and web-researched bridge "
        "information into a BridgeInventory object. Return token_name, protocols, and failed_route_pairs. "
        "Each protocol entry must include its name, official_url when known, whether it is project_recommended, "
        "notes, and a routes list. Each route must include source chain, destination chain, bridge_name, "
        "estimated_time_seconds, fee_usd, and source attribution (lifi, grok, or both). "
        "If a raw route document indicates an API failure, record that pair in failed_route_pairs instead of "
        "treating it as evidence that no bridge exists. Deduplicate overlapping Li.Fi and web-research results."
    )
    rules = (NoInformationLoss, CiteExactAddresses)

    token_name: str = Field(description="Token name")

"""Prompt spec for Step 5: Audit research."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import DeploymentsDocument
from .components import BlockchainResearcher, CiteWebSources, MarkdownOutput, PreserveNegativeResults


class AuditResearchSpec(PromptSpec):
    """Search for smart contract security audits for a specific scope."""

    role = BlockchainResearcher
    input_documents = (DeploymentsDocument,)
    task = (
        "Search for published smart contract security audits covering the scope identified in context. "
        "Extract: auditor name, audit date, scope/contract(s) covered, summary of key findings, "
        "severity breakdown (critical/high/medium/low), and link to the full audit report. "
        "If no audit is found, explicitly state that no audit was discovered for this scope."
    )
    rules = (CiteWebSources, PreserveNegativeResults)
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Audit Results\n\n"
        "## Findings Summary\n\n"
        "## Report Links"
    )

    scope_type: str = Field(description="Audit scope type: 'core', 'chain', or 'bridge'")
    scope_name: str = Field(
        description="Specific scope identifier (e.g., 'PancakeSwap core', 'Arbitrum deployment', 'Stargate bridge')"
    )
    token_name: str = Field(description="Token name for search context")

"""Prompt spec for Step 4: Chain security assessment."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import DeploymentsDocument
from .components import BlockchainResearcher, CiteWebSources, MarkdownOutput


class ChainAssessmentSpec(PromptSpec):
    """Research and assess a blockchain's security and maturity for token deployment."""

    role = BlockchainResearcher
    input_documents = (DeploymentsDocument,)
    task = (
        "Research and produce a security/maturity assessment for the blockchain identified in context. "
        "Cover: chain maturity and track record, total value locked (TVL), history of security incidents, "
        "consensus mechanism, validator/sequencer decentralization, finality guarantees, "
        "EVM compatibility level (if applicable), and overall risk rating."
    )
    rules = (CiteWebSources,)
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Chain Overview\n\n"
        "## Security Track Record\n\n"
        "## Technical Assessment\n\n"
        "## Risk Rating"
    )

    chain_name: str = Field(description="Name of the blockchain being assessed (e.g., Arbitrum)")

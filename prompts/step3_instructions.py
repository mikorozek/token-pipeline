"""Prompt spec for Step 3: Transfer instruction generation."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import BridgesDocument
from .components import CiteExactAddresses, MarkdownOutput, TechnicalDocumentWriter


class TransferInstructionsSpec(PromptSpec):
    """Generate step-by-step transfer instructions for a specific bridge protocol."""

    role = TechnicalDocumentWriter
    input_documents = (BridgesDocument,)
    task = (
        "Generate clear, actionable step-by-step transfer instructions for the bridge protocol "
        "identified in context. Write for a user who has a wallet and wants to bridge the token. "
        "Include: prerequisites, approval steps, transaction steps, expected confirmation times, "
        "fee expectations, and any gotchas or warnings."
    )
    rules = (CiteExactAddresses,)
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Prerequisites\n\n"
        "## Step-by-Step Instructions\n\n"
        "## Fees & Timing\n\n"
        "## Warnings"
    )

    bridge_protocol: str = Field(
        description="Name of the bridge protocol (e.g., Stargate, LayerZero OFT)"
    )
    token_name: str = Field(description="Token name")

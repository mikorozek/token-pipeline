"""Prompt specs for Step 6: Report generation (3 phases)."""

from ai_pipeline_core import PromptSpec
from pydantic import Field

from ..documents import (
    AuditResearchDocument,
    BridgesDocument,
    ChainAssessmentDocument,
    DeploymentsDocument,
    TransferInstructionsDocument,
)
from .components import CiteExactAddresses, MarkdownOutput, SecurityAnalyst


class IssuesFindingsSpec(PromptSpec):
    """Analyze all accumulated data and extract every issue, risk, and notable finding."""

    role = SecurityAnalyst
    input_documents = (
        DeploymentsDocument,
        BridgesDocument,
        TransferInstructionsDocument,
        ChainAssessmentDocument,
        AuditResearchDocument,
    )
    task = (
        "Analyze all provided documents and extract every issue, risk, and notable finding. "
        "Categories include: unaudited deployments, bridge security concerns, chain security incidents, "
        "missing audit coverage, conflicting data between sources, unusual deployment patterns, "
        "and any other concerns. Produce a comprehensive list — do not filter at this stage."
    )
    rules = (CiteExactAddresses,)
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Security Issues\n\n"
        "## Risk Factors\n\n"
        "## Data Quality Concerns\n\n"
        "## Notable Findings"
    )

    token_name: str = Field(description="Token name")


class ImportanceFilteringSpec(PromptSpec, follows=IssuesFindingsSpec):
    """Rank and filter findings by importance for the final report."""

    task = (
        "Review the issues and findings from the previous analysis. Rank each finding by materiality "
        "and importance. Classify as: Critical (immediate user risk), High (significant concern), "
        "Medium (notable but manageable), Low (informational). Filter out noise and duplicate findings. "
        "The output guides the final report, but the report author retains access to all raw data."
    )
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Critical Findings\n\n"
        "## High Importance\n\n"
        "## Medium Importance\n\n"
        "## Low / Informational"
    )


class FinalReportSpec(PromptSpec, follows=ImportanceFilteringSpec):
    """Generate the final cross-chain token security assessment report."""

    task = (
        "Generate a comprehensive cross-chain token assessment report. The filtered findings "
        "document highlights the most important issues, but all raw data is available in context. "
        "Apply independent judgment about what to include. The report should be actionable for "
        "someone evaluating whether to hold or bridge this token."
    )
    output_rules = (MarkdownOutput,)
    output_structure = (
        "## Executive Summary\n\n"
        "## Token Deployments\n\n"
        "## Bridge Map\n\n"
        "## Chain Risk Assessments\n\n"
        "## Audit Coverage\n\n"
        "## Recommended Transfer Paths\n\n"
        "## Risks and Gaps\n\n"
        "## Appendix: Data Sources"
    )

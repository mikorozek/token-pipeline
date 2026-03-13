"""Flow 6: Generate the final report in 3 sequential phases."""

from ai_pipeline_core import Conversation, PipelineFlow, find_document, get_pipeline_logger

from ..documents import (
    AuditResearchDocument,
    BridgesDocument,
    ChainAssessmentDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    FilteredFindingsDocument,
    FinalReportDocument,
    IssuesFindingsDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
    TransferInstructionsDocument,
)
from ..options import CrossChainOptions
from ..prompts.step6_report import FinalReportSpec, ImportanceFilteringSpec, IssuesFindingsSpec

logger = get_pipeline_logger(__name__)


class ReportGenerationFlow(PipelineFlow):
    """Step 6: Generate the final report in 3 sequential phases."""

    estimated_minutes = 5.0

    async def run(
        self,
        run_id: str,
        documents: list[
            DiscoveryRequestDocument
            | DeploymentsDocument
            | BridgesDocument
            | TransferInstructionsDocument
            | ChainAssessmentDocument
            | AuditResearchDocument
            | PipelineConfigDocument
            | TokenIdentityDocument
        ],
        options: CrossChainOptions,
    ) -> list[IssuesFindingsDocument | FilteredFindingsDocument | FinalReportDocument]:
        config_doc = find_document(documents, PipelineConfigDocument)
        cfg = config_doc.parsed
        token_doc = find_document(documents, TokenIdentityDocument)
        identity = token_doc.parsed

        # Collect all context documents (exclude the raw input)
        all_context_docs = [
            d for d in documents if not isinstance(d, DiscoveryRequestDocument | PipelineConfigDocument)
        ]

        # Single Conversation across all 3 phases for prefix caching
        conv = Conversation(model=cfg.formatting_model).with_substitutor(False)

        # Phase 1: Issues & Findings (gemini-3-flash)
        conv = await conv.send_spec(
            IssuesFindingsSpec(token_name=identity.name),
            documents=all_context_docs,
        )
        issues_doc = IssuesFindingsDocument.derive(
            from_documents=tuple(all_context_docs),
            name="issues_findings.md",
            content=conv.content,
            description="Phase 1: All issues and findings",
        )

        # Phase 2: Importance Filtering (gemini-3-flash, follows Phase 1)
        conv = await conv.send_spec(ImportanceFilteringSpec())
        filtered_doc = FilteredFindingsDocument.derive(
            from_documents=(issues_doc,),
            name="filtered_findings.md",
            content=conv.content,
            description="Phase 2: Ranked and filtered findings",
        )

        # Phase 3: Final Report (gpt-5.1, follows Phase 2)
        conv = conv.with_model(cfg.final_report_model)
        conv = await conv.send_spec(FinalReportSpec())
        report_doc = FinalReportDocument.derive(
            from_documents=(filtered_doc, *tuple(all_context_docs)),
            name="final_report.md",
            content=conv.content,
            description=f"Final report: {identity.name} cross-chain assessment",
        )

        return [issues_doc, filtered_doc, report_doc]

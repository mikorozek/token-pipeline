"""Pipeline deployment for cross-chain token discovery."""

import contextlib
from collections.abc import Sequence

from ai_pipeline_core import (
    DeploymentResult,
    Document,
    LimitKind,
    PipelineDeployment,
    PipelineFlow,
    PipelineLimit,
)
from ai_pipeline_core.deployment import FlowAction, FlowDirective

from .documents import (
    AuditResearchDocument,
    BridgesDocument,
    ChainAssessmentDocument,
    DeploymentsDocument,
    FinalReportDocument,
    TransferInstructionsDocument,
)
from .flows.f01_gather_deployments import GatherDeploymentsFlow
from .flows.f02_gather_bridges import GatherBridgesFlow
from .flows.f03_transfer_instructions import TransferInstructionsFlow
from .flows.f04_chain_assessments import ChainAssessmentsFlow
from .flows.f05_audit_research import AuditResearchFlow
from .flows.f06_report import ReportGenerationFlow
from .options import CrossChainOptions


class CrossChainResult(DeploymentResult):
    """Result of the cross-chain token discovery pipeline."""

    deployment_count: int = 0
    bridge_protocol_count: int = 0
    chain_assessment_count: int = 0
    audit_count: int = 0


class CrossChainTokenDiscovery(PipelineDeployment[CrossChainOptions, CrossChainResult]):
    concurrency_limits = {
        "lifi-api": PipelineLimit(60, LimitKind.PER_MINUTE, timeout=120),
    }

    def build_flows(self, options: CrossChainOptions) -> Sequence[PipelineFlow]:
        return [
            GatherDeploymentsFlow(),
            GatherBridgesFlow(),
            TransferInstructionsFlow(),
            ChainAssessmentsFlow(),
            AuditResearchFlow(),
            ReportGenerationFlow(),
        ]

    def plan_next_flow(
        self,
        flow_class: type[PipelineFlow],
        plan: Sequence[PipelineFlow],
        output_documents: list[Document],
    ) -> FlowDirective:
        """Skip TransferInstructionsFlow if no bridge protocols were found."""
        if flow_class is TransferInstructionsFlow:
            bridges = [d for d in output_documents if isinstance(d, BridgesDocument)]
            if bridges and not bridges[0].parsed.protocols:
                return FlowDirective(action=FlowAction.SKIP, reason="No bridge protocols found")
        return FlowDirective()

    @staticmethod
    def build_result(
        run_id: str,
        documents: list[Document],
        options: CrossChainOptions,
    ) -> CrossChainResult:
        report_docs = [d for d in documents if isinstance(d, FinalReportDocument)]
        deployments = [d for d in documents if isinstance(d, DeploymentsDocument)]
        instructions = [d for d in documents if isinstance(d, TransferInstructionsDocument)]
        assessments = [d for d in documents if isinstance(d, ChainAssessmentDocument)]
        audits = [d for d in documents if isinstance(d, AuditResearchDocument)]

        dep_count = 0
        if deployments:
            with contextlib.suppress(Exception):
                dep_count = len(deployments[0].parsed.deployments)

        return CrossChainResult(
            success=len(report_docs) > 0,
            deployment_count=dep_count,
            bridge_protocol_count=len(instructions),
            chain_assessment_count=len(assessments),
            audit_count=len(audits),
        )

"""Flow 5: Research security audits for token, chains, and bridges."""

from typing import cast

from ai_pipeline_core import Document, PipelineFlow, TaskHandle, collect_tasks, find_document, get_pipeline_logger

from ..documents import (
    AuditResearchDocument,
    BridgesDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..options import CrossChainOptions
from ..tasks.step5 import ResearchAuditTask

logger = get_pipeline_logger(__name__)


class AuditResearchFlow(PipelineFlow):
    """Step 5: Research security audits for token, chains, and bridges."""

    estimated_minutes = 5.0

    async def run(
        self,
        run_id: str,
        documents: list[
            DiscoveryRequestDocument
            | DeploymentsDocument
            | BridgesDocument
            | PipelineConfigDocument
            | TokenIdentityDocument
        ],
        options: CrossChainOptions,
    ) -> list[AuditResearchDocument]:
        deployments_doc = find_document(documents, DeploymentsDocument)
        config_doc = find_document(documents, PipelineConfigDocument)
        token_doc = find_document(documents, TokenIdentityDocument)
        identity = token_doc.parsed
        inventory = deployments_doc.parsed

        chain_names = sorted({d.chain_name for d in inventory.deployments})

        bridges_doc = find_document(documents, BridgesDocument)
        bridge_protocols = sorted(protocol.name for protocol in bridges_doc.parsed.protocols)

        handles: list[TaskHandle[list[Document]]] = []

        # 5a: Core token contract
        handles.append(
            cast(
                TaskHandle[list[Document]],
                ResearchAuditTask.run(
                    [deployments_doc, config_doc],
                    scope_type="core",
                    scope_name=f"{identity.name} core",
                    token_name=identity.name,
                ),
            )
        )

        # 5b: Per-chain deployments
        for chain in chain_names:
            handles.append(
                cast(
                    TaskHandle[list[Document]],
                    ResearchAuditTask.run(
                        [deployments_doc, config_doc],
                        scope_type="chain",
                        scope_name=f"{chain} deployment",
                        token_name=identity.name,
                    ),
                )
            )

        # 5c: Per-bridge protocols
        for protocol in bridge_protocols:
            handles.append(
                cast(
                    TaskHandle[list[Document]],
                    ResearchAuditTask.run(
                        [deployments_doc, config_doc],
                        scope_type="bridge",
                        scope_name=f"{protocol} bridge",
                        token_name=identity.name,
                    ),
                )
            )

        total = len(handles)
        logger.info(
            "Launching %d audit research tasks (1 core + %d chains + %d bridges)",
            total,
            len(chain_names),
            len(bridge_protocols),
        )

        batch = await collect_tasks(*handles)
        results: list[AuditResearchDocument] = []
        for doc_list in batch.completed:
            results.extend(cast(list[AuditResearchDocument], doc_list))

        if batch.incomplete:
            logger.warning("%d/%d audit tasks failed", len(batch.incomplete), total)

        return results

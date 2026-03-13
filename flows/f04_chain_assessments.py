"""Flow 4: Assess each chain where the token is deployed."""

from typing import cast

from ai_pipeline_core import Document, PipelineFlow, TaskHandle, collect_tasks, find_document, get_pipeline_logger

from ..documents import (
    ChainAssessmentDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..options import CrossChainOptions
from ..tasks.step4 import AssessChainTask

logger = get_pipeline_logger(__name__)


class ChainAssessmentsFlow(PipelineFlow):
    """Step 4: Assess each chain where the token is deployed."""

    estimated_minutes = 3.0

    async def run(
        self,
        run_id: str,
        documents: list[
            DiscoveryRequestDocument | DeploymentsDocument | PipelineConfigDocument | TokenIdentityDocument
        ],
        options: CrossChainOptions,
    ) -> list[ChainAssessmentDocument]:
        deployments_doc = find_document(documents, DeploymentsDocument)
        config_doc = find_document(documents, PipelineConfigDocument)
        inventory = deployments_doc.parsed

        chain_names = sorted({d.chain_name for d in inventory.deployments})

        logger.info("Assessing %d chains: %s", len(chain_names), ", ".join(chain_names))

        handles = [
            cast(TaskHandle[list[Document]], AssessChainTask.run([deployments_doc, config_doc], chain_name=chain))
            for chain in chain_names
        ]

        batch = await collect_tasks(*handles)
        results: list[ChainAssessmentDocument] = []
        for doc_list in batch.completed:
            results.extend(cast(list[ChainAssessmentDocument], doc_list))

        if batch.incomplete:
            logger.warning("%d chain assessment tasks failed", len(batch.incomplete))

        return results

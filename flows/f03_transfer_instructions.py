"""Flow 3: Generate transfer instructions for each bridge protocol."""

from typing import cast

from ai_pipeline_core import Document, PipelineFlow, TaskHandle, collect_tasks, find_document, get_pipeline_logger

from ..documents import (
    BridgesDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
    TransferInstructionsDocument,
)
from ..options import CrossChainOptions
from ..tasks.step3 import WriteTransferInstructionsTask

logger = get_pipeline_logger(__name__)


class TransferInstructionsFlow(PipelineFlow):
    """Step 3: Generate transfer instructions for each bridge protocol."""

    estimated_minutes = 2.0

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
    ) -> list[TransferInstructionsDocument]:
        bridges_doc = find_document(documents, BridgesDocument)
        config_doc = find_document(documents, PipelineConfigDocument)
        token_doc = find_document(documents, TokenIdentityDocument)
        identity = token_doc.parsed

        bridge_protocols = sorted(protocol.name for protocol in bridges_doc.parsed.protocols)

        if not bridge_protocols:
            logger.warning("No bridge protocols found in bridges document")
            return []

        logger.info(
            "Generating transfer instructions for %d protocols: %s",
            len(bridge_protocols),
            ", ".join(bridge_protocols),
        )

        handles = [
            cast(
                TaskHandle[list[Document]],
                WriteTransferInstructionsTask.run(
                    [bridges_doc, config_doc],
                    bridge_protocol=protocol,
                    token_name=identity.name,
                ),
            )
            for protocol in bridge_protocols
        ]

        batch = await collect_tasks(*handles)
        results: list[TransferInstructionsDocument] = []
        for doc_list in batch.completed:
            results.extend(cast(list[TransferInstructionsDocument], doc_list))

        if batch.incomplete:
            logger.warning("%d transfer instruction tasks failed", len(batch.incomplete))

        return results

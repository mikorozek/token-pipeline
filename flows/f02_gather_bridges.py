"""Flow 2: Discover all bridge routes between token deployments."""

from typing import cast

from ai_pipeline_core import Document, PipelineFlow, TaskHandle, collect_tasks, find_document, get_pipeline_logger

from ..documents import (
    BridgeResearchDocument,
    BridgeRoutesRawDocument,
    BridgesDocument,
    ChainMapDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..options import CrossChainOptions
from ..tasks.step2 import ConsolidateBridgesTask, FetchBridgeRoutesTask, SearchBridgesTask

logger = get_pipeline_logger(__name__)


class GatherBridgesFlow(PipelineFlow):
    """Step 2: Discover all bridge routes between token deployments."""

    estimated_minutes = 5.0

    async def run(
        self,
        run_id: str,
        documents: list[
            DiscoveryRequestDocument
            | DeploymentsDocument
            | ChainMapDocument
            | PipelineConfigDocument
            | TokenIdentityDocument
        ],
        options: CrossChainOptions,
    ) -> list[BridgeRoutesRawDocument | BridgeResearchDocument | BridgesDocument]:
        deployments_doc = find_document(documents, DeploymentsDocument)
        chain_map_doc = find_document(documents, ChainMapDocument)
        config_doc = find_document(documents, PipelineConfigDocument)
        token_doc = find_document(documents, TokenIdentityDocument)
        identity = token_doc.parsed

        inventory = deployments_doc.parsed
        deps = inventory.deployments

        # Only route between chains Li.Fi knows about
        lifi_chain_ids = {c.id for c in chain_map_doc.parsed.chains}
        routable = [d for d in deps if d.chain_id in lifi_chain_ids]

        pairs = []
        for i, src in enumerate(routable):
            for dst in routable[i + 1 :]:
                pairs.append((src, dst))
                pairs.append((dst, src))

        logger.info("Querying %d bridge route pairs for %d routable deployments", len(pairs), len(routable))

        # 2a: Parallel route fetches
        route_handles: list[TaskHandle[list[Document]]] = []
        for src, dst in pairs:
            from_amount = str(10**src.decimals)
            h = cast(
                TaskHandle[list[Document]],
                FetchBridgeRoutesTask.run(
                    [deployments_doc, config_doc],
                    from_chain_id=src.chain_id,
                    from_token=src.address,
                    to_chain_id=dst.chain_id,
                    to_token=dst.address,
                    from_amount=from_amount,
                ),
            )
            route_handles.append(h)

        # 2b: Grok bridge search in parallel with route fetches
        grok_handle = cast(
            TaskHandle[list[Document]],
            SearchBridgesTask.run(
                [token_doc, config_doc],
                token_name=identity.name,
                token_symbol=identity.symbol,
            ),
        )

        batch = await collect_tasks(*route_handles, grok_handle, deadline_seconds=300)

        route_docs: list[BridgeRoutesRawDocument] = []
        research_doc: BridgeResearchDocument | None = None

        for doc_list in batch.completed:
            for doc in doc_list:
                if isinstance(doc, BridgeRoutesRawDocument):
                    route_docs.append(doc)
                elif isinstance(doc, BridgeResearchDocument):
                    research_doc = doc

        if batch.incomplete:
            logger.warning("%d bridge tasks did not complete", len(batch.incomplete))

        if research_doc is None:
            research_doc = BridgeResearchDocument.derive(
                from_documents=(token_doc,),
                name=f"bridge_research_{identity.name.lower().replace(' ', '_')}.md",
                content="Web bridge research unavailable because the search task failed.",
                description=f"Fallback bridge research placeholder for {identity.name}",
            )

        # 2c: Consolidate
        consolidated_results = await ConsolidateBridgesTask.run(
            [*route_docs, research_doc, chain_map_doc, config_doc],
            token_name=identity.name,
        )
        bridges_doc = consolidated_results[0]

        return [*route_docs, research_doc, bridges_doc]

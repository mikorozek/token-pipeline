"""Flow 1: Gather all token deployments across chains."""

from typing import cast

from ai_pipeline_core import Document, PipelineFlow, TaskHandle, collect_tasks, find_document, get_pipeline_logger

from ..documents import (
    ChainMapDocument,
    DeploymentResearchDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    LifiDeploymentsDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..models import DeploymentResearch
from ..options import CrossChainOptions
from ..tasks.step1 import (
    ConsolidateDeploymentsTask,
    FetchChainMapTask,
    FetchLifiDeploymentsTask,
    ResolveTokenIdentityTask,
    SearchDeploymentsTask,
)

logger = get_pipeline_logger(__name__)


class GatherDeploymentsFlow(PipelineFlow):
    """Step 1: Resolve token identity and gather all deployments across chains."""

    estimated_minutes = 3.0

    async def run(
        self,
        run_id: str,
        documents: list[DiscoveryRequestDocument | PipelineConfigDocument],
        options: CrossChainOptions,
    ) -> list[
        ChainMapDocument
        | TokenIdentityDocument
        | LifiDeploymentsDocument
        | DeploymentResearchDocument
        | DeploymentsDocument
    ]:
        input_doc = find_document(documents, DiscoveryRequestDocument)
        config_doc = find_document(documents, PipelineConfigDocument)
        request = input_doc.parsed

        # 1c: Fetch chain map
        chain_map_results = await FetchChainMapTask.run([input_doc, config_doc])
        chain_map_doc = chain_map_results[0]
        chain_map = chain_map_doc.parsed

        # Resolve user's chain name to chain ID
        chain_id = request.chain_id
        if chain_id == 0:
            for chain in chain_map.chains:
                if chain.key.lower() == request.chain_name.lower() or chain.name.lower() == request.chain_name.lower():
                    chain_id = chain.id
                    break
            if chain_id == 0:
                raise ValueError(
                    f"Chain '{request.chain_name}' not found in Li.Fi chain map. "
                    f"Available: {', '.join(c.key for c in chain_map.chains[:20])}..."
                )

        # 1a: Resolve token identity
        identity_results = await ResolveTokenIdentityTask.run([input_doc, config_doc], chain_id=chain_id)
        token_doc = identity_results[0]
        identity = token_doc.parsed

        # 1b + 1d: Li.Fi deployments + Grok search in parallel
        h_lifi = cast(
            TaskHandle[list[Document]],
            FetchLifiDeploymentsTask.run(
                [input_doc, token_doc, config_doc],
                coin_key=identity.coin_key,
                source_chain_id=identity.chain_id,
                source_address=identity.address,
                source_decimals=identity.decimals,
            ),
        )
        h_grok = cast(
            TaskHandle[list[Document]],
            SearchDeploymentsTask.run(
                [token_doc, config_doc],
                token_name=identity.name,
                token_symbol=identity.symbol,
            ),
        )
        batch = await collect_tasks(h_lifi, h_grok)

        lifi_doc: LifiDeploymentsDocument | None = None
        research_doc: DeploymentResearchDocument | None = None

        for doc_list in batch.completed:
            for doc in doc_list:
                if isinstance(doc, LifiDeploymentsDocument):
                    lifi_doc = doc
                elif isinstance(doc, DeploymentResearchDocument):
                    research_doc = doc

        if batch.incomplete:
            logger.warning("%d deployment tasks did not complete", len(batch.incomplete))

        if lifi_doc is None:
            raise RuntimeError("Li.Fi deployment discovery did not complete")
        if research_doc is None:
            research_doc = DeploymentResearchDocument.derive(
                from_documents=(token_doc,),
                name=f"deployment_research_{identity.name.lower().replace(' ', '_')}.json",
                content=DeploymentResearch(
                    observed_deployments=[],
                    notes="Web deployment research unavailable because the search task failed.",
                ),
                description=f"Fallback deployment research placeholder for {identity.name}",
            )

        # 1e: Consolidate
        consolidated_results = await ConsolidateDeploymentsTask.run(
            [lifi_doc, research_doc, chain_map_doc, config_doc, token_doc],
            token_name=identity.name,
            token_symbol=identity.symbol,
        )
        deployments_doc = consolidated_results[0]

        return [chain_map_doc, token_doc, lifi_doc, research_doc, deployments_doc]

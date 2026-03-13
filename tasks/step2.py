"""Tasks for Step 2: Bridge route discovery and consolidation."""

from ai_pipeline_core import Conversation, ModelOptions, PipelineTask, find_document, get_pipeline_logger

from ..documents import (
    BridgeResearchDocument,
    BridgeRoutesRawDocument,
    BridgesDocument,
    ChainMapDocument,
    DeploymentsDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..lifi_client import LiFiClient
from ..models import BridgeInventory
from ..prompts.step2_bridges import BridgeSearchSpec, ConsolidateBridgesSpec

logger = get_pipeline_logger(__name__)


class FetchBridgeRoutesTask(PipelineTask):
    """Fetch Li.Fi bridge routes for a single deployment pair."""

    retries = 2
    retry_delay_seconds = 10
    timeout_seconds = 60

    @classmethod
    async def run(
        cls,
        documents: list[DeploymentsDocument | PipelineConfigDocument],
        from_chain_id: int,
        from_token: str,
        to_chain_id: int,
        to_token: str,
        from_amount: str,
    ) -> list[BridgeRoutesRawDocument]:
        deployments_doc = find_document(documents, DeploymentsDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        client = LiFiClient(base_url=cfg.lifi_base_url, timeout=cfg.lifi_timeout_seconds)

        raw: dict[str, object]
        try:
            raw = await client.fetch_routes(
                from_chain_id,
                from_token,
                to_chain_id,
                to_token,
                from_amount,
            )
        except Exception as exc:
            logger.warning(
                "Route query failed for %d→%d: %s. Recording request failure metadata.",
                from_chain_id,
                to_chain_id,
                exc,
            )
            raw = {
                "routes": [],
                "_status": "request_failed",
                "_error": str(exc),
            }

        api_url = f"https://li.quest/v1/advanced/routes?from={from_chain_id}&to={to_chain_id}"
        routes = raw.get("routes", [])
        routes_count = len(routes) if isinstance(routes, list) else 0

        return [
            BridgeRoutesRawDocument.create(
                name=f"routes_{from_chain_id}_{to_chain_id}.json",
                content=raw,
                derived_from=(deployments_doc.sha256, api_url),
                description=f"Bridge routes {from_chain_id}→{to_chain_id}: {routes_count} routes",
            )
        ]


class SearchBridgesTask(PipelineTask):
    """Search web for project-specific bridge info via Grok."""

    retries = 1
    timeout_seconds = 180

    @classmethod
    async def run(
        cls,
        documents: list[TokenIdentityDocument | PipelineConfigDocument],
        token_name: str,
        token_symbol: str,
    ) -> list[BridgeResearchDocument]:
        token_doc = find_document(documents, TokenIdentityDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        model_options = ModelOptions(search_context_size=cfg.search_context_size)

        conv = Conversation(model=cfg.search_model, model_options=model_options)
        conv = await conv.send_spec(
            BridgeSearchSpec(token_name=token_name, token_symbol=token_symbol),
            documents=[token_doc],
        )

        citation_urls = tuple(c.url for c in conv.citations)
        derived = (token_doc.sha256,) + citation_urls

        return [
            BridgeResearchDocument.create(
                name=f"bridge_research_{token_name.lower().replace(' ', '_')}.md",
                content=conv.content,
                derived_from=derived,
                description=f"Bridge research for {token_name}",
            )
        ]


class ConsolidateBridgesTask(PipelineTask):
    """Consolidate Li.Fi routes + Grok bridge research using gemini-3-flash."""

    timeout_seconds = 120

    @classmethod
    async def run(
        cls,
        documents: list[BridgeRoutesRawDocument | BridgeResearchDocument | ChainMapDocument | PipelineConfigDocument],
        token_name: str,
    ) -> list[BridgesDocument]:
        chain_map_doc = find_document(documents, ChainMapDocument)
        research_doc = find_document(documents, BridgeResearchDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        route_docs = [doc for doc in documents if isinstance(doc, BridgeRoutesRawDocument)]

        conv = Conversation(model=cfg.formatting_model).with_substitutor(False)
        conv = await conv.send_spec(
            ConsolidateBridgesSpec(token_name=token_name),
            documents=[chain_map_doc, research_doc, *route_docs],
        )
        parsed = conv.parsed
        if parsed is None:
            raise RuntimeError("Structured bridge consolidation returned no parsed payload")
        if not isinstance(parsed, BridgeInventory):
            raise TypeError(f"Expected BridgeInventory, got {type(parsed).__name__}")

        all_source_docs = (chain_map_doc, research_doc, *route_docs)
        return [
            BridgesDocument.derive(
                from_documents=all_source_docs,
                name="bridges.json",
                content=parsed,
                description=f"Consolidated bridges for {token_name}",
            )
        ]

"""Tasks for Step 1: Token deployment discovery and consolidation."""

from ai_pipeline_core import Conversation, ModelOptions, PipelineTask, find_document, get_pipeline_logger

from ..documents import (
    ChainMapDocument,
    DeploymentResearchDocument,
    DeploymentsDocument,
    DiscoveryRequestDocument,
    LifiDeploymentsDocument,
    PipelineConfigDocument,
    TokenIdentityDocument,
)
from ..lifi_client import LiFiClient
from ..models import ChainInfo, ChainMap, DeploymentInventory, DeploymentResearch, TokenIdentity
from ..prompts.step1_deployments import ConsolidateDeploymentsSpec, DeploymentSearchSpec

logger = get_pipeline_logger(__name__)


def _dedupe_urls(urls: tuple[str, ...] | list[str]) -> list[str]:
    """Preserve first-seen order while removing empty and duplicate URLs."""

    deduped: list[str] = []
    for url in urls:
        cleaned = url.strip()
        if cleaned and cleaned not in deduped:
            deduped.append(cleaned)
    return deduped


def _attach_citation_urls(research: DeploymentResearch, citation_urls: tuple[str, ...]) -> DeploymentResearch:
    """Use model citations as a fallback evidence set for observed deployments."""

    if not citation_urls:
        return research

    fallback_urls = _dedupe_urls(citation_urls)
    observed_deployments = [
        deployment.model_copy(
            update={
                "source_urls": _dedupe_urls(deployment.source_urls) or fallback_urls,
            }
        )
        for deployment in research.observed_deployments
    ]
    return research.model_copy(update={"observed_deployments": observed_deployments})


class FetchChainMapTask(PipelineTask):
    """Fetch Li.Fi chain ID → name mapping."""

    retries = 2
    retry_delay_seconds = 10
    timeout_seconds = 60

    @classmethod
    async def run(
        cls,
        documents: list[DiscoveryRequestDocument | PipelineConfigDocument],
    ) -> list[ChainMapDocument]:
        input_doc = find_document(documents, DiscoveryRequestDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        client = LiFiClient(base_url=cfg.lifi_base_url, timeout=cfg.lifi_timeout_seconds)
        raw = await client.fetch_chains()

        chain_list = raw.get("chains", raw) if isinstance(raw, dict) else raw
        chains = [ChainInfo(id=c["id"], name=c["name"], key=c.get("key", "")) for c in chain_list]

        return [
            ChainMapDocument.derive(
                from_documents=(input_doc,),
                name="chain_map.json",
                content=ChainMap(chains=chains),
                description=f"Li.Fi chain map ({len(chains)} chains)",
            )
        ]


class ResolveTokenIdentityTask(PipelineTask):
    """Resolve token identity via Li.Fi /token endpoint."""

    retries = 2
    retry_delay_seconds = 10
    timeout_seconds = 60

    @classmethod
    async def run(
        cls,
        documents: list[DiscoveryRequestDocument | PipelineConfigDocument],
        chain_id: int,
    ) -> list[TokenIdentityDocument]:
        input_doc = find_document(documents, DiscoveryRequestDocument)
        request = input_doc.parsed
        cfg = find_document(documents, PipelineConfigDocument).parsed
        client = LiFiClient(base_url=cfg.lifi_base_url, timeout=cfg.lifi_timeout_seconds)
        raw = await client.resolve_token(chain_id, request.contract_address)

        identity = TokenIdentity(
            address=raw["address"],
            chain_id=raw["chainId"],
            coin_key=raw.get("coinKey"),
            name=raw.get("name", "Unknown"),
            symbol=raw.get("symbol", "???"),
            decimals=raw.get("decimals", 18),
            logo_uri=raw.get("logoURI", ""),
        )

        return [
            TokenIdentityDocument.derive(
                from_documents=(input_doc,),
                name="token_identity.json",
                content=identity,
                description=f"Token: {identity.name} ({identity.symbol})",
            )
        ]


class FetchLifiDeploymentsTask(PipelineTask):
    """Fetch all token deployments via Li.Fi /tokens, filtered by coinKey."""

    retries = 1
    timeout_seconds = 120

    @classmethod
    async def run(
        cls,
        documents: list[DiscoveryRequestDocument | TokenIdentityDocument | PipelineConfigDocument],
        coin_key: str | None,
        source_chain_id: int,
        source_address: str,
        source_decimals: int,
    ) -> list[LifiDeploymentsDocument]:
        input_doc = find_document(documents, DiscoveryRequestDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        client = LiFiClient(base_url=cfg.lifi_base_url, timeout=cfg.lifi_timeout_seconds)

        deployments_data: list[dict[str, object]] = [
            {"chainId": source_chain_id, "address": source_address, "decimals": source_decimals}
        ]

        if coin_key:
            raw = await client.fetch_tokens()
            tokens_by_chain: dict[str, list[dict[str, object]]] = raw.get("tokens", {})
            for chain_id_str, token_list in tokens_by_chain.items():
                for token in token_list:
                    if token.get("coinKey") == coin_key:
                        entry = {
                            "chainId": int(chain_id_str),
                            "address": token["address"],
                            "decimals": token.get("decimals", 18),
                        }
                        if not (
                            entry["chainId"] == source_chain_id
                            and str(entry["address"]).lower() == source_address.lower()
                        ):
                            deployments_data.append(entry)

        return [
            LifiDeploymentsDocument.derive(
                from_documents=(input_doc,),
                name="lifi_deployments.json",
                content=deployments_data,
                description=f"Li.Fi deployments: {len(deployments_data)} found (coinKey={coin_key})",
            )
        ]


class SearchDeploymentsTask(PipelineTask):
    """Search web for additional deployments via Grok."""

    retries = 1
    timeout_seconds = 180

    @classmethod
    async def run(
        cls,
        documents: list[TokenIdentityDocument | PipelineConfigDocument],
        token_name: str,
        token_symbol: str,
    ) -> list[DeploymentResearchDocument]:
        token_doc = find_document(documents, TokenIdentityDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        model_options = ModelOptions(search_context_size=cfg.search_context_size)

        conv = Conversation(model=cfg.search_model, model_options=model_options)
        conv = await conv.send_spec(
            DeploymentSearchSpec(token_name=token_name, token_symbol=token_symbol),
            documents=[token_doc],
        )

        citation_urls = tuple(c.url for c in conv.citations)
        derived = tuple(d.sha256 for d in documents) + citation_urls
        parsed = conv.parsed
        if parsed is None:
            raise RuntimeError("Structured deployment search returned no parsed payload")
        if not isinstance(parsed, DeploymentResearch):
            raise TypeError(f"Expected DeploymentResearch, got {type(parsed).__name__}")
        parsed = _attach_citation_urls(parsed, citation_urls)

        return [
            DeploymentResearchDocument.create(
                name=f"deployment_research_{token_name.lower().replace(' ', '_')}.json",
                content=parsed,
                derived_from=derived,
                description=f"Web-searched deployments for {token_name}",
            )
        ]


class ConsolidateDeploymentsTask(PipelineTask):
    """Consolidate Li.Fi + Grok deployment data using gemini-3-flash."""

    timeout_seconds = 120

    @classmethod
    async def run(
        cls,
        documents: list[
            LifiDeploymentsDocument
            | DeploymentResearchDocument
            | ChainMapDocument
            | PipelineConfigDocument
            | TokenIdentityDocument
        ],
        token_name: str,
        token_symbol: str,
    ) -> list[DeploymentsDocument]:
        lifi_doc = find_document(documents, LifiDeploymentsDocument)
        research_doc = find_document(documents, DeploymentResearchDocument)
        chain_map_doc = find_document(documents, ChainMapDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed

        conv = Conversation(model=cfg.formatting_model).with_substitutor(False)
        conv = await conv.send_spec(
            ConsolidateDeploymentsSpec(token_name=token_name, token_symbol=token_symbol),
            documents=[lifi_doc, research_doc, chain_map_doc],
        )
        parsed = conv.parsed
        if parsed is None:
            raise RuntimeError("Structured deployment consolidation returned no parsed payload")
        if not isinstance(parsed, DeploymentInventory):
            raise TypeError(f"Expected DeploymentInventory, got {type(parsed).__name__}")

        return [
            DeploymentsDocument.derive(
                from_documents=(lifi_doc, research_doc, chain_map_doc),
                name="deployments.json",
                content=parsed,
                description=f"Consolidated deployments for {token_name}",
            )
        ]

"""Tasks for Step 4: Chain security assessment."""

from ai_pipeline_core import Conversation, ModelOptions, PipelineTask, find_document

from ..documents import ChainAssessmentDocument, DeploymentsDocument, PipelineConfigDocument
from ..prompts.step4_assessment import ChainAssessmentSpec


class AssessChainTask(PipelineTask):
    """Assess a single chain's security and maturity via Grok web search."""

    retries = 1
    timeout_seconds = 180

    @classmethod
    async def run(
        cls,
        documents: list[DeploymentsDocument | PipelineConfigDocument],
        chain_name: str,
    ) -> list[ChainAssessmentDocument]:
        deployments_doc = find_document(documents, DeploymentsDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        model_options = ModelOptions(search_context_size=cfg.search_context_size)

        conv = Conversation(model=cfg.search_model, model_options=model_options)
        conv = await conv.send_spec(
            ChainAssessmentSpec(chain_name=chain_name),
            documents=[deployments_doc],
        )

        citation_urls = tuple(c.url for c in conv.citations)
        derived = (deployments_doc.sha256,) + citation_urls

        return [
            ChainAssessmentDocument.create(
                name=f"chain_{chain_name.lower().replace(' ', '_')}.md",
                content=conv.content,
                derived_from=derived,
                description=f"Chain assessment: {chain_name}",
            )
        ]

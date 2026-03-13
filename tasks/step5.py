"""Tasks for Step 5: Audit research."""

from ai_pipeline_core import Conversation, ModelOptions, PipelineTask, find_document

from ..documents import AuditResearchDocument, DeploymentsDocument, PipelineConfigDocument
from ..prompts.step5_audit import AuditResearchSpec


class ResearchAuditTask(PipelineTask):
    """Research audits for a single scope via Grok web search."""

    retries = 1
    timeout_seconds = 180

    @classmethod
    async def run(
        cls,
        documents: list[DeploymentsDocument | PipelineConfigDocument],
        scope_type: str,
        scope_name: str,
        token_name: str,
    ) -> list[AuditResearchDocument]:
        input_doc = find_document(documents, DeploymentsDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed
        model_options = ModelOptions(search_context_size=cfg.search_context_size)

        conv = Conversation(model=cfg.search_model, model_options=model_options)
        conv = await conv.send_spec(
            AuditResearchSpec(
                scope_type=scope_type,
                scope_name=scope_name,
                token_name=token_name,
            ),
            documents=[input_doc],
        )

        citation_urls = tuple(c.url for c in conv.citations)
        derived = (input_doc.sha256,) + citation_urls

        return [
            AuditResearchDocument.create(
                name=f"audit_{scope_type}_{scope_name.lower().replace(' ', '_')}.md",
                content=conv.content,
                derived_from=derived,
                description=f"Audit research: {scope_type}/{scope_name}",
            )
        ]

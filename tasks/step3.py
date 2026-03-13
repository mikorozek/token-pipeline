"""Tasks for Step 3: Transfer instruction generation."""

from ai_pipeline_core import Conversation, PipelineTask, find_document

from ..documents import BridgesDocument, PipelineConfigDocument, TransferInstructionsDocument
from ..prompts.step3_instructions import TransferInstructionsSpec


class WriteTransferInstructionsTask(PipelineTask):
    """Generate transfer instructions for a single bridge protocol."""

    timeout_seconds = 120

    @classmethod
    async def run(
        cls,
        documents: list[BridgesDocument | PipelineConfigDocument],
        bridge_protocol: str,
        token_name: str,
    ) -> list[TransferInstructionsDocument]:
        bridges_doc = find_document(documents, BridgesDocument)
        cfg = find_document(documents, PipelineConfigDocument).parsed

        conv = Conversation(model=cfg.formatting_model).with_substitutor(False)
        conv = await conv.send_spec(
            TransferInstructionsSpec(bridge_protocol=bridge_protocol, token_name=token_name),
            documents=[bridges_doc],
        )

        return [
            TransferInstructionsDocument.derive(
                from_documents=(bridges_doc,),
                name=f"transfer_{bridge_protocol.lower().replace(' ', '_')}.md",
                content=conv.content,
                description=f"Transfer instructions: {bridge_protocol}",
            )
        ]

"""CLI entry point for the cross-chain token discovery pipeline."""

from ai_pipeline_core import Document, get_pipeline_logger, setup_logging

from .deployment import CrossChainTokenDiscovery
from .documents import DiscoveryRequestDocument, PipelineConfigDocument
from .models import DiscoveryRequest, PipelineConfig
from .options import CrossChainCliArgs, CrossChainOptions

setup_logging(level="INFO")
logger = get_pipeline_logger(__name__)

# Well-known chain name → ID mappings for the initializer.
# The full Li.Fi map is fetched in Step 1c.
_CHAIN_ALIASES: dict[str, int] = {
    "ethereum": 1,
    "eth": 1,
    "bsc": 56,
    "bnb": 56,
    "polygon": 137,
    "matic": 137,
    "arbitrum": 42161,
    "arb": 42161,
    "optimism": 10,
    "op": 10,
    "avalanche": 43114,
    "avax": 43114,
    "base": 8453,
    "scroll": 534352,
    "linea": 59144,
    "fantom": 250,
    "ftm": 250,
    "gnosis": 100,
    "xdai": 100,
}


def initialize(options: CrossChainOptions) -> tuple[str, list[Document]]:
    """CLI initializer: create run_id and root input document from options.

    The framework dynamically merges CrossChainCliArgs into the options object,
    so contract_address and chain_name are available at runtime via the mixin.
    """
    # cli_mixin fields are merged into options at runtime by the framework
    chain_name: str = getattr(options, "chain_name", "").strip().lower()
    chain_id = _CHAIN_ALIASES.get(chain_name, 0)

    address: str = getattr(options, "contract_address", "").strip()
    if not address:
        raise ValueError("contract_address is required")
    if not chain_name:
        raise ValueError("chain_name is required")
    run_id = f"{address[:8]}-{chain_name}"

    input_doc = DiscoveryRequestDocument.create_root(
        name="input.json",
        content=DiscoveryRequest(
            contract_address=address,
            chain_name=chain_name,
            chain_id=chain_id,
        ),
        reason=f"CLI input: {address} on {chain_name}",
    )
    config_doc = PipelineConfigDocument.create_root(
        name="pipeline_config.json",
        content=PipelineConfig(
            search_model=options.search_model,
            formatting_model=options.formatting_model,
            final_report_model=options.final_report_model,
            lifi_base_url=options.lifi_base_url,
            lifi_timeout_seconds=options.lifi_timeout_seconds,
            search_context_size=options.search_context_size,
        ),
        reason="Pipeline runtime configuration",
    )

    logger.info(
        "Pipeline: %s on %s (chain_id=%d, resolve=%s)",
        address,
        chain_name,
        chain_id,
        "yes" if chain_id == 0 else "no",
    )
    return run_id, [config_doc, input_doc]


CrossChainTokenDiscovery().run_cli(
    initializer=initialize,
    cli_mixin=CrossChainCliArgs,
    trace_name="cross-chain-token",
)

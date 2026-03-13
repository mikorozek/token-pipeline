"""Deployment-level configuration and CLI arguments."""

from typing import Literal

from ai_pipeline_core import FlowOptions
from pydantic_settings import BaseSettings


class CrossChainOptions(FlowOptions):
    """Deployment-level configuration. All fields overridable via env vars."""

    search_model: str = "grok-4.1-fast-search"
    formatting_model: str = "gemini-3-flash"
    final_report_model: str = "gpt-5.1"
    lifi_base_url: str = "https://li.quest/v1"
    lifi_timeout_seconds: int = 30
    search_context_size: Literal["low", "medium", "high"] = "high"


class CrossChainCliArgs(BaseSettings):
    """CLI arguments parsed by run_cli(cli_mixin=...)."""

    contract_address: str
    chain_name: str

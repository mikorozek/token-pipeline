"""Async Li.Fi API client. All methods acquire the 'lifi-api' concurrency slot."""

import httpx
from ai_pipeline_core import get_pipeline_logger, pipeline_concurrency

logger = get_pipeline_logger(__name__)

LIFI_BASE_URL = "https://li.quest/v1"
DEFAULT_TIMEOUT = 30
TOKENS_TIMEOUT = 60


class LiFiClient:
    """Async Li.Fi API client with rate-limited access."""

    def __init__(self, base_url: str = LIFI_BASE_URL, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._tokens_timeout = max(timeout, TOKENS_TIMEOUT)

    async def resolve_token(self, chain_id: int, address: str) -> dict:
        """GET /token — resolve token identity."""
        async with pipeline_concurrency("lifi-api"), httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(
                f"{self._base_url}/token",
                params={"chain": chain_id, "token": address},
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def fetch_chains(self) -> dict:
        """GET /chains — chain ID → name mapping."""
        async with pipeline_concurrency("lifi-api"), httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(f"{self._base_url}/chains")
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def fetch_tokens(self) -> dict:
        """GET /tokens — full token list (large payload)."""
        async with pipeline_concurrency("lifi-api"), httpx.AsyncClient(timeout=self._tokens_timeout) as client:
            resp = await client.get(f"{self._base_url}/tokens")
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    async def fetch_routes(
        self,
        from_chain_id: int,
        from_token: str,
        to_chain_id: int,
        to_token: str,
        from_amount: str,
    ) -> dict:
        """POST /advanced/routes — bridge routes between two deployments."""
        async with pipeline_concurrency("lifi-api"), httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base_url}/advanced/routes",
                json={
                    "fromChainId": from_chain_id,
                    "fromTokenAddress": from_token,
                    "toChainId": to_chain_id,
                    "toTokenAddress": to_token,
                    "fromAmount": from_amount,
                },
            )
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

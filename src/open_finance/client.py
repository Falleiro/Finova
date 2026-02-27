"""
Async HTTP client wrapper for the Open Finance API.
All other open_finance modules use this client to make requests.
"""

import logging
from typing import Any

import httpx

from src.config import settings

logger = logging.getLogger(__name__)

_BASE_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}


class OpenFinanceClient:
    def __init__(self) -> None:
        self._base_url = settings.open_finance_base_url.rstrip("/")
        self._client_id = settings.open_finance_client_id
        self._client_secret = settings.open_finance_client_secret
        self._consent_token = settings.open_finance_consent_token
        self._access_token: str | None = None

    async def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        async with httpx.AsyncClient(timeout=15) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/auth",
                    json={
                        "clientId": self._client_id,
                        "clientSecret": self._client_secret,
                    },
                )
                response.raise_for_status()
                self._access_token = response.json()["apiKey"]
                return self._access_token
            except httpx.HTTPError as exc:
                logger.error("Failed to obtain access token: %s", exc)
                raise

    async def get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        token = await self._get_access_token()
        headers = {
            **_BASE_HEADERS,
            "X-API-KEY": token,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.get(
                    f"{self._base_url}{path}",
                    headers=headers,
                    params=params or {},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    # Token may have expired — force refresh on next call
                    self._access_token = None
                logger.error("HTTP error from Open Finance API [%s %s]: %s", path, exc.response.status_code, exc)
                raise
            except httpx.RequestError as exc:
                logger.error("Network error contacting Open Finance API [%s]: %s", path, exc)
                raise


# Module-level singleton
client = OpenFinanceClient()

from __future__ import annotations

import asyncio
from time import monotonic
from typing import Any

import httpx

from .client import SlidingWindowLimiter
from .models import PairSnapshot

HOLDER_CHAIN_IDS: dict[str, int] = {
    "ethereum": 1,
    "bsc": 56,
    "polygon": 137,
    "avalanche": 43114,
    "arbitrum": 42161,
    "base": 8453,
    "optimism": 10,
    "linea": 59144,
    "blast": 81457,
    "zksync": 324,
    "mantle": 5000,
}

HOLDER_CACHE_TTL_SECONDS = 15 * 60
HOLDER_REQUEST_TIMEOUT_SECONDS = 6.0
HOLDER_REQUESTS_PER_MINUTE = 45
HOLDER_SOURCE = "honeypot.is"

_holder_limiter = SlidingWindowLimiter(HOLDER_REQUESTS_PER_MINUTE)
_holder_cache_lock = asyncio.Lock()
_holder_cache: dict[tuple[str, str], tuple[float, int | None, str | None]] = {}


def _cache_key(chain_id: str, token_address: str) -> tuple[str, str]:
    return chain_id.strip().lower(), token_address.strip().lower()


async def _cache_get(chain_id: str, token_address: str) -> tuple[int | None, str | None] | None:
    key = _cache_key(chain_id, token_address)
    async with _holder_cache_lock:
        item = _holder_cache.get(key)
        if not item:
            return None
        expires_at, holders_count, holders_source = item
        if monotonic() >= expires_at:
            _holder_cache.pop(key, None)
            return None
        return holders_count, holders_source


async def _cache_set(chain_id: str, token_address: str, holders_count: int | None, holders_source: str | None) -> None:
    key = _cache_key(chain_id, token_address)
    async with _holder_cache_lock:
        _holder_cache[key] = (
            monotonic() + HOLDER_CACHE_TTL_SECONDS,
            holders_count,
            holders_source,
        )


def _parse_holders_count(payload: dict[str, Any]) -> int | None:
    token = payload.get("token")
    if isinstance(token, dict):
        raw = token.get("totalHolders")
        try:
            if raw is None:
                return None
            return int(raw)
        except (TypeError, ValueError):
            return None
    return None


async def fetch_holder_count(
    chain_id: str,
    token_address: str,
    *,
    client: httpx.AsyncClient | None = None,
) -> tuple[int | None, str | None]:
    normalized_chain = chain_id.strip().lower()
    normalized_token = token_address.strip()
    if not normalized_token:
        return None, None

    chain_numeric = HOLDER_CHAIN_IDS.get(normalized_chain)
    if chain_numeric is None:
        return None, "unsupported-chain"

    cached = await _cache_get(normalized_chain, normalized_token)
    if cached is not None:
        return cached

    own_client = client is None
    http_client = client
    if http_client is None:
        http_client = httpx.AsyncClient(
            base_url="https://api.honeypot.is",
            timeout=httpx.Timeout(HOLDER_REQUEST_TIMEOUT_SECONDS),
            headers={"Accept": "application/json"},
        )

    try:
        await _holder_limiter.acquire()
        response = await http_client.get(
            "/v2/IsHoneypot",
            params={"address": normalized_token, "chainID": str(chain_numeric)},
        )
        if response.status_code >= 400:
            await _cache_set(normalized_chain, normalized_token, None, "unavailable")
            return None, "unavailable"
        payload = response.json()
        holders_count = _parse_holders_count(payload if isinstance(payload, dict) else {})
        await _cache_set(normalized_chain, normalized_token, holders_count, HOLDER_SOURCE)
        return holders_count, HOLDER_SOURCE
    except Exception:
        await _cache_set(normalized_chain, normalized_token, None, "unavailable")
        return None, "unavailable"
    finally:
        if own_client and http_client is not None:
            await http_client.aclose()


async def hydrate_pair_holders(pairs: list[PairSnapshot], *, max_pairs: int | None = None) -> None:
    if not pairs:
        return

    grouped: dict[tuple[str, str], list[PairSnapshot]] = {}
    for pair in pairs:
        if pair.holders_count is not None:
            continue
        token = pair.base_address.strip()
        chain = pair.chain_id.strip().lower()
        if not token:
            continue
        grouped.setdefault((chain, token.lower()), []).append(pair)

    if not grouped:
        return

    # Prioritize rows with the strongest current flow first.
    ordered = sorted(
        grouped.items(),
        key=lambda item: max(
            (p.volume_h1 + p.volume_h24 * 0.1 + p.liquidity_usd * 0.01 + p.txns_h1 * 10.0)
            for p in item[1]
        ),
        reverse=True,
    )
    if max_pairs is not None and max_pairs > 0:
        ordered = ordered[:max_pairs]

    semaphore = asyncio.Semaphore(8)
    async with httpx.AsyncClient(
        base_url="https://api.honeypot.is",
        timeout=httpx.Timeout(HOLDER_REQUEST_TIMEOUT_SECONDS),
        headers={"Accept": "application/json"},
    ) as client:
        async def worker(chain: str, token: str, bucket: list[PairSnapshot]) -> None:
            async with semaphore:
                holders_count, holders_source = await fetch_holder_count(chain, token, client=client)
                for pair in bucket:
                    pair.holders_count = holders_count
                    pair.holders_source = holders_source

        await asyncio.gather(*(worker(chain, token, rows) for (chain, token), rows in ordered))


async def hydrate_token_rows_with_holders(
    rows: list[dict[str, object]],
    *,
    chain_field: str = "chainId",
    token_field: str = "tokenAddress",
    holders_field: str = "holdersCount",
    source_field: str = "holdersSource",
    max_rows: int | None = None,
) -> None:
    if not rows:
        return

    unique: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        chain = str(row.get(chain_field, "")).strip().lower()
        token = str(row.get(token_field, "")).strip().lower()
        if not chain or not token:
            continue
        unique.setdefault((chain, token), []).append(row)

    ordered = list(unique.items())
    if max_rows is not None and max_rows > 0:
        ordered = ordered[:max_rows]

    semaphore = asyncio.Semaphore(8)
    async with httpx.AsyncClient(
        base_url="https://api.honeypot.is",
        timeout=httpx.Timeout(HOLDER_REQUEST_TIMEOUT_SECONDS),
        headers={"Accept": "application/json"},
    ) as client:
        async def worker(chain: str, token: str, bucket: list[dict[str, object]]) -> None:
            async with semaphore:
                holders_count, holders_source = await fetch_holder_count(chain, token, client=client)
                for row in bucket:
                    row[holders_field] = holders_count
                    row[source_field] = holders_source

        await asyncio.gather(*(worker(chain, token, bucket) for (chain, token), bucket in ordered))

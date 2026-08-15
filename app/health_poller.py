"""
Real HTTP-based health polling against the other fleet engines.

Replaces the fleet's previous stand-in for this (a hardcoded dict of
"healthy" statuses in app/routers/health.py) with actual GET requests to
each engine's own /health endpoint. A service that's down, unreachable,
or slow is a real, honestly-recorded UNHEALTHY/DEGRADED result - never
silently reported as healthy.
"""

import asyncio
import time

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health_check import HealthCheck, HealthStatus
from app.service_registry import get_service_urls

HEALTH_PATH = "/health"
POLL_TIMEOUT_SECONDS = 5.0


async def poll_service(client: httpx.AsyncClient, name: str, base_url: str) -> HealthCheck:
    """
    Poll one service's /health endpoint for real. Never raises - a
    connection failure/timeout is captured as an honest UNHEALTHY record
    rather than propagated, so one down service can't take the whole
    polling pass down with it.
    """
    url = f"{base_url}{HEALTH_PATH}"
    started = time.monotonic()
    details = None

    try:
        response = await client.get(url, timeout=POLL_TIMEOUT_SECONDS)
        elapsed_ms = int((time.monotonic() - started) * 1000)

        if response.status_code == 200:
            status = HealthStatus.HEALTHY
            error_message = None
        else:
            status = HealthStatus.DEGRADED
            error_message = f"HTTP {response.status_code}"

        try:
            details = response.json()
        except ValueError:
            pass

    except httpx.RequestError as exc:
        elapsed_ms = int((time.monotonic() - started) * 1000)
        status = HealthStatus.UNHEALTHY
        error_message = f"{type(exc).__name__}: {exc}"
        logger.warning(f"Health poll failed for {name} ({url}): {error_message}")

    return HealthCheck(
        service_name=name,
        service_type="engine",
        service_url=url,
        status=status,
        response_time_ms=elapsed_ms,
        details=details,
        error_message=error_message,
    )


async def poll_all_services(db: AsyncSession) -> list[HealthCheck]:
    """Poll every registered service concurrently and persist a HealthCheck row per service."""
    service_urls = get_service_urls()

    async with httpx.AsyncClient() as client:
        checks = await asyncio.gather(
            *(poll_service(client, name, base_url) for name, base_url in service_urls.items())
        )

    for check in checks:
        db.add(check)
    await db.commit()
    for check in checks:
        await db.refresh(check)

    return list(checks)


async def poll_one_service(db: AsyncSession, service_name: str) -> HealthCheck | None:
    """Poll a single registered service by name, persist and return its result. None if unknown."""
    service_urls = get_service_urls()
    base_url = service_urls.get(service_name)
    if base_url is None:
        return None

    async with httpx.AsyncClient() as client:
        check = await poll_service(client, service_name, base_url)

    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check

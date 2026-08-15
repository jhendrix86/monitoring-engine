"""
Registry of the other fleet engines this service polls for health.

Ports match the fleet-wide port map (see OS42_ROADMAP.md / each engine's
own docker/docker-compose.yml). Hostnames default to the engine's own
name, matching Docker Compose's `container_name` on the shared
`os42-shared` network - that's how these actually resolve on the real
deployment target (each engine is its own compose project joined to one
external network, so container_name doubles as the DNS name other
containers reach it by).

Deliberately excludes:
- monitoring-engine itself (no self-poll needed - it already reports its
  own liveness via the top-level /health endpoint in app/main.py).
- pricing-intelligence-system: a one-shot CLI batch tool, no FastAPI
  server, nothing to poll.
- funnel_automation_engine and baselayer: each runs its own separate,
  non-consolidated compose stack (deploy/README.md), not on the shared
  os42-shared network by default - polling them would need real,
  separately-configured URLs, not a guess.
"""

import os

SERVICE_PORTS: dict[str, int] = {
    "governance-engine": 8033,
    "kg-service": 8034,
    "global-state-manager": 8035,
    "revenue-operations-engine": 8036,
    "notification-engine": 8037,
    "customer-support-engine": 8038,
    "marketing-automation-engine": 8039,
    "content-engine": 8040,
    "sales-engine": 8041,
    "analytics-engine": 8042,
    "integration-engine": 8044,
    "media-generation-service": 8045,
    "priority-scheduler": 8046,
}

# Overrides the hostname portion for every service in one place - e.g. set
# to "localhost" when running engines directly on one host outside Docker
# (their compose service/container names won't resolve as DNS names in
# that case). Unset (the real-deployment default) uses each service's own
# name as its hostname, matching container_name on the shared network.
_HOST_OVERRIDE = os.environ.get("MONITORING_TARGET_HOST")


def get_service_urls() -> dict[str, str]:
    """Map of service name -> base URL (no trailing slash) to poll for health."""
    host_for = lambda name: _HOST_OVERRIDE or name
    return {
        name: f"http://{host_for(name)}:{port}"
        for name, port in SERVICE_PORTS.items()
    }

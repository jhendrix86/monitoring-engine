"""
Maps this engine's own AlertSeverity onto the fleet's canonical Severity
scale (autonomy-events, added 2026-08-14 - see its severity/__init__.py
for the full story of why a canonical scale exists).

AlertSeverity has 4 levels (info/warning/error/critical) - one fewer than
Severity's 5 (info/low/medium/high/critical), and different vocabulary
for the middle two. There is no natural equivalent of Severity.MEDIUM in
AlertSeverity, and that's an honest, expected consequence of AlertSeverity
being the coarser-grained scale, not a bug in this mapping - not every
canonical level needs to be reachable from every local one.

Ordering follows Python's own logging module convention (which "warning"/
"error" already echo): INFO < WARNING < ERROR < CRITICAL maps onto
INFO < LOW < HIGH < CRITICAL, preserving relative order while skipping
MEDIUM.
"""

from autonomy_events import Severity

from app.models.alert import AlertSeverity

_TO_CANONICAL = {
    AlertSeverity.INFO: Severity.INFO,
    AlertSeverity.WARNING: Severity.LOW,
    AlertSeverity.ERROR: Severity.HIGH,
    AlertSeverity.CRITICAL: Severity.CRITICAL,
}


def to_canonical_severity(severity: AlertSeverity) -> Severity:
    """Convert this engine's AlertSeverity to the fleet's canonical Severity."""
    return _TO_CANONICAL[severity]

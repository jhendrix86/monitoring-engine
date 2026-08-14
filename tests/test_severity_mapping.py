"""
Tests app/severity_mapping.py's conversion of this engine's own
AlertSeverity onto the fleet's canonical Severity scale (autonomy-events,
added 2026-08-14).
"""

import pytest
from autonomy_events import Severity, severity_at_least

from app.models.alert import AlertSeverity
from app.severity_mapping import to_canonical_severity


class TestSeverityMapping:
    @pytest.mark.parametrize(
        "alert_severity,expected",
        [
            (AlertSeverity.INFO, Severity.INFO),
            (AlertSeverity.WARNING, Severity.LOW),
            (AlertSeverity.ERROR, Severity.HIGH),
            (AlertSeverity.CRITICAL, Severity.CRITICAL),
        ],
    )
    def test_every_alert_severity_maps_to_its_canonical_counterpart(self, alert_severity, expected):
        assert to_canonical_severity(alert_severity) == expected

    def test_every_alert_severity_value_is_covered(self):
        for alert_severity in AlertSeverity:
            to_canonical_severity(alert_severity)

    def test_mapping_preserves_relative_order(self):
        # AlertSeverity's own order (info < warning < error < critical)
        # must still hold after mapping, even though a level (MEDIUM) gets
        # skipped over - the point is nothing gets inverted.
        ordered = [AlertSeverity.INFO, AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL]
        mapped = [to_canonical_severity(s) for s in ordered]
        for lower, higher in zip(mapped, mapped[1:]):
            assert severity_at_least(higher, lower)

"""Tests for the Tanzania routing table and cross-border cascades (G8)."""
from africa_coord_bus.event import CoordinationEvent, EventDomain, EventSeverity
from africa_coord_bus.tanzania import (
    CROSS_BORDER_TABLE,
    PORTABLE_PATTERNS,
    TANZANIA_ROUTING_TABLE,
    tanzania_rules,
)


def _ev(domain, etype, sev=EventSeverity.ALERT, **data):
    return CoordinationEvent(domain=domain, event_type=etype, source="test",
                             severity=sev, data=data)


def test_table_populated():
    assert len(TANZANIA_ROUTING_TABLE) >= 8
    assert len(CROSS_BORDER_TABLE) >= 2
    assert len({r.name for r in tanzania_rules()}) == len(tanzania_rules())


def test_livestock_destocking_is_tz_specific():
    """The cascade class Kenya's table never needed."""
    e = _ev(EventDomain.WATER, "drought_alert")
    hits = [r.name for r in TANZANIA_ROUTING_TABLE if r.matches(e)]
    assert "drought→livestock_destocking_tz" in hits


def test_livestock_migration_is_a_health_signal():
    e = _ev(EventDomain.AGRICULTURE, "livestock_migration", sev=EventSeverity.WARNING)
    hits = [r.name for r in TANZANIA_ROUTING_TABLE if r.matches(e)]
    assert "livestock_migration→disease_surveillance_tz" in hits


def test_cross_border_requires_border_adjacent():
    """Cross-border cascades must not fire on ordinary interior events."""
    interior = _ev(EventDomain.WATER, "drought_alert")
    assert [r for r in CROSS_BORDER_TABLE if r.matches(interior)] == []

    border = _ev(EventDomain.WATER, "drought_alert", border_adjacent=True)
    fired = [r.name for r in CROSS_BORDER_TABLE if r.matches(border)]
    assert "xborder:drought→transboundary_migration" in fired


def test_cross_border_outbreak_notifies_neighbour():
    border = _ev(EventDomain.HEALTH, "disease_outbreak", border_adjacent=True)
    fired = [r.name for r in CROSS_BORDER_TABLE if r.matches(border)]
    assert "xborder:outbreak→neighbour_notification" in fired


def test_portable_patterns_documented():
    """The port must record what transfers — that is the standard's payload."""
    assert "*→subnational_authority" in PORTABLE_PATTERNS
    assert "NOT portable" in PORTABLE_PATTERNS["*→subnational_authority"]


def test_helper_includes_cross_border_by_default():
    assert len(tanzania_rules()) == len(TANZANIA_ROUTING_TABLE) + len(CROSS_BORDER_TABLE)
    assert len(tanzania_rules(include_cross_border=False)) == len(TANZANIA_ROUTING_TABLE)

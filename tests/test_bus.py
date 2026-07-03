"""Smoke tests for africa-coord-bus."""
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from africa_coord_bus import (
    EventBus, CoordinationEvent, DomainCascade,
    EventDomain, EventSeverity, KenyaLocation,
)

def test_drought_cascade():
    log = []
    bus = EventBus()
    DomainCascade(bus, action_handler=lambda a, e: log.append(a)).wire_all()
    targets = bus.publish(CoordinationEvent(
        domain=EventDomain.WATER, event_type="drought_alert",
        source="wapimaji-mcp", severity=EventSeverity.ALERT,
        location=KenyaLocation(county="Turkana", county_code=23),
        data={"ndvi_anomaly": -0.28, "spi_3month": -1.8},
    ))
    assert len(targets) >= 4
    assert "bima-mcp.evaluate_parametric_payout" in targets
    assert "afya-mcp.activate_malnutrition_watch" in targets

def test_round_trip():
    e = CoordinationEvent(
        domain=EventDomain.HEALTH, event_type="disease_outbreak",
        source="afya-mcp", severity=EventSeverity.ALERT,
        location=KenyaLocation(county="Kisumu"),
        data={"disease": "cholera"},
    )
    e2 = CoordinationEvent.from_dict(e.to_dict())
    assert e2.event_id == e.event_id
    assert e2.location.county == "Kisumu"

def test_offline_queue(tmp_path):
    q = tmp_path / "queue.jsonl"
    bus = EventBus(queue_path=q)
    bus.publish(CoordinationEvent(
        domain=EventDomain.WATER, event_type="flood_alert",
        source="wapimaji-mcp", severity=EventSeverity.WARNING,
    ))
    assert q.exists()
    assert q.stat().st_size > 0

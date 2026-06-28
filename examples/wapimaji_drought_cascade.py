#!/usr/bin/env python3
"""
End-to-end integration: wapimaji-mcp → africa-coord-bus → cascade

Shows how a drought signal from wapimaji-mcp flows to bima-mcp (insurance),
kilimo-mcp (crop advisory), afya-mcp (malnutrition watch), and county-mcp (alert).

Prerequisites:
    pip install africa-coord-bus
    # wapimaji-mcp v0.1.3+ includes coordination.py
"""
from africa_coord_bus import (
    EventBus, CoordinationEvent, DomainCascade,
    EventDomain, EventSeverity, KenyaLocation
)

def on_action(action: str, event):
    """Replace this with real MCP client calls in production."""
    print(f"  🔔 {action}")
    print(f"     county={event.location.county} | severity={event.severity.value}")
    print(f"     data={event.data}")
    print()

def main():
    # Create bus with offline-first queue
    bus = EventBus(queue_path="/tmp/demo-coord-bus.jsonl")

    # Wire all domain cascade handlers
    cascade = DomainCascade(bus, action_handler=on_action)
    cascade.wire_all()

    print("=" * 60)
    print("Scenario: Drought alert from wapimaji-mcp (Turkana, Phase 3)")
    print("=" * 60)
    print()

    # This is what wapimaji-mcp publishes when drought phase ≥ 2
    targets = bus.publish(CoordinationEvent(
        domain=EventDomain.WATER,
        event_type="drought_alert",
        source="wapimaji-mcp",
        severity=EventSeverity.ALERT,
        location=KenyaLocation(county="Turkana", county_code=23),
        data={
            "ndma_phase": 3,
            "phase_label": "Crisis",
            "rainfall_deficit_pct": 42.0,
            "ndvi_anomaly": -0.28,
            "spi_3month": -1.8,
        },
        requires_action=True,
    ))

    print(f"\n{len(targets)} coordination actions triggered:")
    for t in targets:
        print(f"  → {t}")

    stats = bus.stats()
    print(f"\nBus stats: {stats['published_this_session']} events | "
          f"{stats['routing_rules']} routing rules")
    print()
    print("In production: replace on_action() with real MCP client calls.")
    print("Queue at /tmp/demo-coord-bus.jsonl persists across sessions (offline-first).")

if __name__ == "__main__":
    main()

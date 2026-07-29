# africa-coord-bus

**The coordination layer between East Africa's AI tools.**

31 MCP servers exist for Kenya's coordination domains — payments, water, agriculture, health, land, education. They work in isolation. When `wapimaji-mcp` detects a drought six weeks in advance, `bima-mcp` doesn't know to evaluate parametric insurance payouts. `afya-mcp` doesn't know to activate malnutrition surveillance. `kilimo-mcp` doesn't know to issue drought-resistant crop advisories.

This package provides the event bus that connects them.

## The coordination gap

A smallholder farmer in Turkana has parametric crop insurance. NDVI anomaly data shows drought coming 6 weeks out. The insurance contract says coverage triggers when SPI drops below -1.5.

Without coordination: the farmer finds out the crop is failing at harvest. The insurance company finds out at claims submission. The health system finds out at clinic presentation.

With coordination:

```
wapimaji-mcp → CoordinationEvent(drought_alert, ALERT)
    │
    ├── bima-mcp.evaluate_parametric_payout      (triggered immediately)
    ├── kilimo-mcp.issue_drought_advisory         (farmers receive SMS)
    ├── afya-mcp.activate_malnutrition_watch      (CHWs briefed)
    └── county-mcp.alert_county_health            (county notified)
```

Six weeks earlier. Before the damage is visible.


## AI Agent Compatibility

Model-agnostic. Tested with:

| Model | Notes |
|-------|-------|
| `claude-sonnet-5` | **Recommended** — completes drought→insurance→county cascades end-to-end |
| `claude-opus-4-8` | Highest accuracy for complex multi-domain triage |
| `gemini-flash` | High-volume, cost-sensitive routing |

Sonnet 5 (2026-06-30) is the first Sonnet-class model that reliably
finishes the full multi-server cascade without stopping mid-chain.


## Architecture: Shared Context Store (CA-MCP)

**Research validation:** *Enhancing MCP with Context-Aware Server Collaboration*
(arXiv:2601.11595, January 2026) — introduces **CA-MCP**, adding a Shared Context
Store (SCS) to stateless MCP. Results:

- Statistically significant reduction in **LLM calls** for complex multi-server tasks
- Decreased **response failures** when task conditions are not immediately satisfied
- Validated on TravelPlanner and REALM-Bench benchmarks

`africa-coord-bus` implements a compatible event-driven shared context pattern:
the coordination bus acts as the SCS for cross-domain cascades. A drought event
from `wapimaji-mcp` propagates context (severity, county, affected area) to
`bima-mcp`, `kilimo-mcp`, and `county-mcp` without each server re-establishing
that context independently.

**The disconnected models problem** (Krishnan, arXiv:2504.21030): stateless MCP
servers lack global context — making coordination buses like this one structurally
necessary, not optional, for multi-domain agents in East Africa.

## Install

```bash
pip install africa-coord-bus
```

## Usage

```python
from africa_coord_bus import (
    EventBus, CoordinationEvent, DomainCascade,
    EventDomain, EventSeverity, KenyaLocation
)

# Create bus with offline queue
bus = EventBus(queue_path="/var/coord-bus/queue.jsonl")

# Wire all domain cascade handlers
cascade = DomainCascade(bus)
cascade.wire_all()

# Publish a drought signal from wapimaji-mcp
event = CoordinationEvent(
    domain=EventDomain.WATER,
    event_type="drought_alert",
    source="wapimaji-mcp",
    severity=EventSeverity.ALERT,
    location=KenyaLocation(county="Turkana", county_code=23),
    data={
        "ndvi_anomaly": -0.28,
        "spi_3month": -1.8,
        "rainfall_deficit_pct": 42,
    },
)

targets = bus.publish(event)
# → [WATER→FINANCE] bima-mcp.evaluate_parametric_payout | Turkana | drought_alert | alert
# → [WATER→AGRI]    kilimo-mcp.issue_drought_advisory    | Turkana | drought_alert | alert
# → [WATER→HEALTH]  afya-mcp.activate_malnutrition_watch | Turkana | drought_alert | alert
```

## Built-in routing rules

| Trigger | Cascade |
|---------|---------|
| `water.drought_alert` (WARNING+) | `bima-mcp.evaluate_parametric_payout`, `kilimo-mcp.issue_drought_advisory`, `soko-mcp.price_alert` |
| `water.drought_alert` (ALERT+) | + `afya-mcp.activate_malnutrition_watch`, `county-mcp.alert_county_health` |
| `health.disease_outbreak` (cholera/typhoid) | `wapimaji-mcp.flag_water_risk` |
| `health.disease_outbreak` (WARNING+) | `county-mcp.health_alert`, `fomu-mcp.emergency_procurement` |
| `agriculture.price_spike` (>30% above seasonal) | `afya-mcp.food_security_watch`, `bima-mcp.food_security_eval` |
| `water.flood_alert` (WARNING+) | `afya-mcp.waterborne_watch`, `county-mcp.flood_response` |

Add custom rules:

```python
from africa_coord_bus import RoutingRule, EventDomain, EventSeverity

bus.routing.add(RoutingRule(
    name="outbreak→emergency_procurement",
    description="Disease outbreak triggers essential medicine procurement",
    trigger_domain=EventDomain.HEALTH,
    trigger_event_type="disease_outbreak",
    trigger_min_severity=EventSeverity.ALERT,
    target_actions=["fomu-mcp.emergency_medicine_order"],
))
```

## Offline-first

Events are written to a local queue before dispatch. If dispatch fails, events persist for replay:

```python
bus = EventBus(queue_path="/var/coord-bus/events.jsonl")
# ... system restart ...
bus.replay_queue()  # processes all unhandled events
```

## Related packages

All available at [pypi.org/user/gmahia](https://pypi.org/user/gmahia/):

- `wapimaji-mcp` — drought intelligence (publishes `water.drought_alert`)
- `bima-mcp` — parametric insurance (consumes drought events)
- `kilimo-mcp` — agricultural coordination (consumes drought + price events)
- `afya-mcp` — health coordination (consumes drought + flood + disease events)
- `mpesa-mcp` — M-Pesa payments (handles insurance payouts)

## Integration with wapimaji-mcp

`wapimaji-mcp` v0.1.3+ includes built-in coordination publishing. When drought phase ≥ 2 (Stressed), it automatically fires coordination events:

```python
# wapimaji-mcp now exposes this MCP tool:
result = call_mcp_tool("publish_drought_coordination", {
    "county": "Turkana",
    "phase": 3,
    "rainfall_deficit_pct": 42.0
})
# → fires 5 downstream actions automatically via africa-coord-bus
```

See [examples/wapimaji_drought_cascade.py](examples/wapimaji_drought_cascade.py) for the complete integration.

## IP & Collaboration

MIT licensed. Feedback via GitHub Issues only — pull requests are not accepted. Demo data is labeled DEMO and is not suitable for operational decisions. Full policy: [docs/architecture/IP_POLICY.md](docs/architecture/IP_POLICY.md). Security reports: see [SECURITY.md](SECURITY.md).

<!-- interconnect:v1 -->
## Part of the East Africa coordination stack

- **Install & run:** `pip install reli-cli && reli list` — 33 MCP servers on the [official MCP Registry](https://registry.modelcontextprotocol.io) under `io.github.gabrielmahia`
- **Evaluate any model on Swahili agent tasks:** [kipimo](https://github.com/gabrielmahia/kipimo) · [dataset](https://huggingface.co/datasets/gmahia/kipimo) · [leaderboard](https://huggingface.co/spaces/gmahia/kipimo-leaderboard)
- **Coordinate across servers:** [africa-coord-bus](https://pypi.org/project/africa-coord-bus/) — offline-first event bus with a built-in Kenya routing table
- **Datasets:** [huggingface.co/gmahia](https://huggingface.co/gmahia) · **Docs hub:** [nairobi-stack](https://github.com/gabrielmahia/nairobi-stack)

Model-agnostic by design: closed APIs, open-weight models, and small distilled models are all first-class citizens.
<!-- /interconnect:v1 -->

## Interoperability: CAP 1.2 export

Events can be emitted as OASIS **Common Alerting Protocol (CAP) 1.2** so a county, ministry, or warning network can consume them with existing tools — no need to adopt this bus:

```python
from africa_coord_bus import CoordinationEvent, to_cap_xml
xml = to_cap_xml(event)   # valid CAP 1.2; also to_cap_dict(event)
```

Trust integrity is preserved: a DEMO/synthetic event is emitted as `status=Exercise`, never `Actual`, so a test signal cannot be mistaken for a live public alert.

## Offline sync: conflict-free queue merge (CRDT)

Events are immutable and uuid-keyed, so two offline queues reconcile by union —
a grow-only set (G-Set), the simplest CRDT. `merge_queues` is idempotent,
commutative, and associative, so devices sync in any order and replay is safe:

```python
from africa_coord_bus import merge_queues, write_queue
merged = merge_queues("device_a/queue.jsonl", "device_b/queue.jsonl")  # deduped by event_id
write_queue(merged, "synced/queue.jsonl")
```

## Humanitarian interop: HXL + IPC hint

```python
from africa_coord_bus import to_hxl_row, ipc_severity_hint
to_hxl_row(event)          # HXL-tagged row for HDX / HXL Proxy tooling
ipc_severity_hint(event)   # coarse IPC-phase HINT (food-security domains) — NOT an IPC classification
```
The IPC helper is a legibility hint only; its caveat is embedded in the return
value and it never assigns Phase 5 (Famine), which is a formal analytical act.

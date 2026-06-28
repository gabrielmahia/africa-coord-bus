"""
Routing rules — which domains respond to which events.

Built-in table for Kenya coordination domains.
Designed to be extended by domain implementers.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from .event import CoordinationEvent, EventDomain, EventSeverity


@dataclass
class RoutingRule:
    """A single routing rule: when event matches condition, notify targets."""
    name:        str
    description: str
    trigger_domain:    EventDomain
    trigger_event_type: str          # exact match or "*" for all
    trigger_min_severity: EventSeverity = EventSeverity.WARNING
    target_domains:  list[EventDomain] = field(default_factory=list)
    target_actions:  list[str]         = field(default_factory=list)
    condition:       Callable[[CoordinationEvent], bool] | None = None

    def matches(self, event: CoordinationEvent) -> bool:
        if event.domain != self.trigger_domain:
            return False
        if self.trigger_event_type != "*" and event.event_type != self.trigger_event_type:
            return False
        severities = [s.value for s in EventSeverity]
        if severities.index(event.severity.value if hasattr(event.severity, 'value') else event.severity) \
           < severities.index(self.trigger_min_severity.value):
            return False
        if self.condition and not self.condition(event):
            return False
        return True


# ── Kenya coordination routing table ──────────────────────────
KENYA_ROUTING_TABLE: list[RoutingRule] = [

    # ── Drought cascade ───────────────────────────────────────
    RoutingRule(
        name="drought→parametric_insurance",
        description=(
            "When drought early warning fires (NDVI anomaly + SPI threshold), "
            "trigger parametric insurance evaluation in bima-mcp. "
            "Insurance payout does not require claims adjuster — satellite confirms."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.FINANCE],
        target_actions=["bima-mcp.evaluate_parametric_payout"],
    ),

    RoutingRule(
        name="drought→crop_advisory",
        description=(
            "When drought confirmed, kilimo-mcp issues drought-resistant crop advisory "
            "and early harvest guidance to registered farmers in affected counties."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.AGRICULTURE],
        target_actions=["kilimo-mcp.issue_drought_advisory", "soko-mcp.price_alert"],
    ),

    RoutingRule(
        name="drought→malnutrition_surveillance",
        description=(
            "Drought triggers acute malnutrition risk within 6-8 weeks. "
            "afya-mcp activates CHW malnutrition surveillance protocol "
            "before visible symptoms appear."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.HEALTH],
        target_actions=["afya-mcp.activate_malnutrition_watch", "county-mcp.alert_county_health"],
    ),

    # ── Disease outbreak cascade ───────────────────────────────
    RoutingRule(
        name="disease_outbreak→water_quality",
        description=(
            "Cholera and typhoid outbreaks are waterborne. "
            "Disease signal triggers water source inspection and protection protocol."
        ),
        trigger_domain=EventDomain.HEALTH,
        trigger_event_type="disease_outbreak",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.WATER],
        target_actions=["wapimaji-mcp.flag_water_risk"],
        condition=lambda e: any(d in str(e.data.get("disease", "")).lower()
                               for d in ["cholera", "typhoid", "dysentery"]),
    ),

    RoutingRule(
        name="disease_outbreak→county_alert",
        description=(
            "Disease outbreak triggers county health office alert and procurement "
            "of essential medicines via fomu-mcp."
        ),
        trigger_domain=EventDomain.HEALTH,
        trigger_event_type="disease_outbreak",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.CIVIC, EventDomain.PROCUREMENT],
        target_actions=["county-mcp.health_alert", "fomu-mcp.emergency_procurement"],
    ),

    # ── Price spike cascade ────────────────────────────────────
    RoutingRule(
        name="price_spike→food_security",
        description=(
            "Maize price spike >30% above seasonal mean indicates food security stress. "
            "Triggers afya-mcp malnutrition watch and kilimo-mcp market advisory."
        ),
        trigger_domain=EventDomain.AGRICULTURE,
        trigger_event_type="price_spike",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.HEALTH, EventDomain.FINANCE],
        target_actions=["afya-mcp.food_security_watch", "bima-mcp.food_security_eval"],
        condition=lambda e: e.data.get("pct_above_seasonal", 0) >= 30,
    ),

    # ── Flash flood cascade ────────────────────────────────────
    RoutingRule(
        name="flood→disease_risk",
        description=(
            "Flash floods create waterborne disease risk within 2-4 weeks. "
            "Early activation of CHW surveillance and water protection protocols."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="flood_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.HEALTH, EventDomain.CIVIC],
        target_actions=["afya-mcp.waterborne_watch", "county-mcp.flood_response"],
    ),
]


class RoutingRules:
    """Manages and evaluates coordination routing rules."""

    def __init__(self, rules: list[RoutingRule] | None = None):
        self.rules = rules if rules is not None else KENYA_ROUTING_TABLE[:]

    def add(self, rule: RoutingRule) -> None:
        self.rules.append(rule)

    def evaluate(self, event: CoordinationEvent) -> list[RoutingRule]:
        """Return all rules that match this event."""
        return [r for r in self.rules if r.matches(event)]

    def get_targets(self, event: CoordinationEvent) -> list[str]:
        """Return all target actions from matching rules."""
        targets = []
        for rule in self.evaluate(event):
            targets.extend(rule.target_actions)
        return list(dict.fromkeys(targets))  # deduplicate, preserve order

"""
Tanzania coordination routing table — second-country port (Gap Register G8).

WHY THIS EXISTS
---------------
A coordination standard with one implementation is a prototype. With two, the
country-specific parts separate from the portable parts, and the pattern becomes
something a third country can adopt without the original authors.

This module does three things:

1. TANZANIA_ROUTING_TABLE — Tanzania's own cascades, reflecting its actual
   coordination realities (central-corridor drought, delta flooding, recurrent
   cholera, and a pastoralist livestock economy that Kenya's table does not model).

2. CROSS_BORDER_TABLE — cascades that no single-country table can express.
   Drought across the Kenya–Tanzania rangeland is one event, not two: pastoralist
   herds migrate across the border ahead of the drought, moving disease and grazing
   pressure with them. This is the first thing the second implementation unlocked.

3. PORTABLE_PATTERNS — what survived the port, documented for country #3.

WHAT THE PORT REVEALED (honest findings, see docs/PORTING_GUIDE.md)
-------------------------------------------------------------------
- PORTABLE: drought→insurance, drought→crop advisory, outbreak→water quality,
  price_spike→food security. These are hazard physics + market logic; they
  transfer with only threshold changes.
- NOT PORTABLE: the administrative target. Kenya cascades to counties; Tanzania
  cascades to regions (mikoa) and districts (wilaya). Any table that hardcodes
  "county" is not a standard — it is a Kenya table. This is the single biggest
  lesson of the port.
- NEW IN TZ: livestock/pastoralist cascades. Kenya's table has no livestock
  domain trigger; Tanzania's economy requires it. Country #3 should expect to
  find at least one cascade class its predecessors did not need.

- THE HARD FINDING (type-level Kenya lock-in): CoordinationEvent.location is
  typed `KenyaLocation`, with fields `county` and `sub_county`. The bus does not
  merely *default* to Kenya — it encodes Kenya in the type system. Tanzania has
  regions (mikoa) and districts (wilaya), not counties. This is invisible until
  someone actually ports, which is the entire argument for doing a second country
  before calling the pattern a standard.

  Deliberately NOT fixed here: renaming the type would break every existing
  consumer, and this table must not regress a working system. The correct fix is
  a backwards-compatible `SubnationalLocation` with `KenyaLocation` retained as
  an alias — proposed, not imposed, and tracked in the Gap Register. Tanzania
  rules therefore carry location in `event.data` until that lands.
"""

from __future__ import annotations

from .event import CoordinationEvent, EventDomain, EventSeverity
from .routing import RoutingRule

# ── Tanzania coordination routing table ───────────────────────────────

TANZANIA_ROUTING_TABLE: list[RoutingRule] = [

    # ── Drought cascade (central semi-arid corridor: Dodoma, Singida, Shinyanga)
    RoutingRule(
        name="drought→parametric_insurance_tz",
        description=(
            "Drought early warning (TMA seasonal forecast + vegetation anomaly) triggers "
            "parametric insurance evaluation. Portable from Kenya: same hazard physics, "
            "different thresholds — TZ's unimodal south needs a longer confirmation window "
            "than Kenya's bimodal rainfall."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.FINANCE],
        target_actions=["bima-mcp.evaluate_parametric_payout"],
    ),

    RoutingRule(
        name="drought→crop_advisory_tz",
        description=(
            "Drought confirmed: issue drought-tolerant crop advisory. TZ staple mix is "
            "cassava/sorghum-weighted where Kenya leans maize, so the advisory content "
            "differs even though the cascade shape is identical."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.AGRICULTURE],
        target_actions=["kilimo-mcp.issue_drought_advisory"],
    ),

    # ── Livestock / pastoralist cascade — NEW, not present in Kenya's table ──
    RoutingRule(
        name="drought→livestock_destocking_tz",
        description=(
            "Drought in rangeland districts triggers early-destocking advisory and "
            "livestock market coordination. Selling before condition collapses preserves "
            "household capital; waiting destroys it. This cascade class did not exist in "
            "the Kenya table and is the clearest evidence that country #3 will surface "
            "cascades its predecessors never needed."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.AGRICULTURE, EventDomain.FINANCE],
        target_actions=[
            "kilimo-mcp.issue_destocking_advisory",
            "soko-mcp.open_livestock_market_window",
        ],
    ),

    RoutingRule(
        name="livestock_migration→disease_surveillance_tz",
        description=(
            "Pastoralist herd movement concentrates animals and people at water points, "
            "raising zoonotic and waterborne transmission risk along the migration route. "
            "Movement is a health signal, not only an agricultural one."
        ),
        trigger_domain=EventDomain.AGRICULTURE,
        trigger_event_type="livestock_migration",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.HEALTH, EventDomain.WATER],
        target_actions=[
            "afya-mcp.raise_surveillance_along_corridor",
            "wapimaji-mcp.check_water_point_capacity",
        ],
    ),

    # ── Flood cascade (Rufiji / Kilombero basins, coastal lowlands) ──────
    RoutingRule(
        name="flood→disease_risk_tz",
        description=(
            "Flooding contaminates shallow wells and displaces households. Cholera is "
            "recurrent in TZ's flood-prone basins, so the flood→outbreak lead time is the "
            "operative window: act on the flood warning, not the first case."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="flood_alert",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.HEALTH],
        target_actions=[
            "afya-mcp.preposition_cholera_supplies",
            "wapimaji-mcp.flag_contaminated_sources",
        ],
    ),

    RoutingRule(
        name="flood→transport_disruption_tz",
        description=(
            "Basin flooding cuts feeder roads, which is what actually breaks the response: "
            "supplies cannot reach the district even when they exist. Route to transport "
            "before the health response is dispatched, not after it fails."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="flood_alert",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.TRANSPORT, EventDomain.PROCUREMENT],
        target_actions=[
            "usafiri-mcp.assess_route_passability",
            "ugavi-mcp.reroute_supply_delivery",
        ],
    ),

    # ── Outbreak cascade ────────────────────────────────────────────────
    RoutingRule(
        name="disease_outbreak→water_quality_tz",
        description=(
            "Waterborne outbreak triggers source testing. Portable from Kenya unchanged — "
            "the causal chain between contaminated source and case cluster is not "
            "country-specific."
        ),
        trigger_domain=EventDomain.HEALTH,
        trigger_event_type="disease_outbreak",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.WATER],
        target_actions=["wapimaji-mcp.test_water_sources"],
    ),

    RoutingRule(
        name="disease_outbreak→region_alert_tz",
        description=(
            "Outbreak escalation notifies the REGION (mkoa) and district (wilaya) — not a "
            "county. Kenya's table cascades to counties; that target is the least portable "
            "part of any national routing table."
        ),
        trigger_domain=EventDomain.HEALTH,
        trigger_event_type="disease_outbreak",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.CIVIC, EventDomain.PROCUREMENT],
        target_actions=[
            "county-mcp.notify_subnational_authority",  # generic: region/district in TZ
            "ugavi-mcp.check_medical_stock",
        ],
    ),

    # ── Market cascade ──────────────────────────────────────────────────
    RoutingRule(
        name="price_spike→food_security_tz",
        description=(
            "Staple price spike is an early food-insecurity signal. Portable from Kenya; "
            "only the staple basket changes."
        ),
        trigger_domain=EventDomain.FINANCE,
        trigger_event_type="price_spike",
        trigger_min_severity=EventSeverity.WARNING,
        target_domains=[EventDomain.AGRICULTURE, EventDomain.HEALTH],
        target_actions=[
            "soko-mcp.flag_staple_price_anomaly",
            "afya-mcp.raise_malnutrition_surveillance",
        ],
    ),
]


# ── Cross-border table — what a SECOND country unlocks ────────────────
#
# These cascades are structurally impossible to express in a single-country
# table. The Kenya–Tanzania rangeland is one ecological and pastoralist system;
# a drought does not stop at the border, and neither do the herds.

CROSS_BORDER_TABLE: list[RoutingRule] = [

    RoutingRule(
        name="xborder:drought→transboundary_migration",
        description=(
            "Severe drought on either side of the KE–TZ rangeland precedes cross-border "
            "herd movement toward remaining pasture and water. The receiving side needs "
            "warning BEFORE arrival — grazing pressure, water-point crowding, and disease "
            "risk all land on a district that had no drought of its own. Single-country "
            "tables cannot see this; it is the first cascade the second implementation "
            "made expressible."
        ),
        trigger_domain=EventDomain.WATER,
        trigger_event_type="drought_alert",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.AGRICULTURE, EventDomain.HEALTH, EventDomain.CIVIC],
        target_actions=[
            "kilimo-mcp.warn_receiving_districts",
            "afya-mcp.raise_surveillance_along_corridor",
            "county-mcp.notify_subnational_authority",
        ],
        condition=lambda e: bool((e.data or {}).get("border_adjacent")),
    ),

    RoutingRule(
        name="xborder:outbreak→neighbour_notification",
        description=(
            "An outbreak in a border district is a regional event. Notifying only the "
            "national authority routes the alert away from the districts physically "
            "closest to it, which may sit in the neighbouring country."
        ),
        trigger_domain=EventDomain.HEALTH,
        trigger_event_type="disease_outbreak",
        trigger_min_severity=EventSeverity.ALERT,
        target_domains=[EventDomain.HEALTH, EventDomain.CIVIC],
        target_actions=[
            "afya-mcp.notify_cross_border_districts",
            "county-mcp.notify_subnational_authority",
        ],
        condition=lambda e: bool((e.data or {}).get("border_adjacent")),
    ),
]


# ── What survived the port (for country #3) ───────────────────────────

PORTABLE_PATTERNS: dict[str, str] = {
    "drought→parametric_insurance": "Portable. Hazard physics + payout logic. Change thresholds only.",
    "drought→crop_advisory":        "Portable. Change the staple basket, keep the cascade.",
    "disease_outbreak→water_quality": "Portable unchanged. Causal chain is not country-specific.",
    "price_spike→food_security":   "Portable. Change the staple basket.",
    "flood→disease_risk":          "Portable. Lead time varies with basin hydrology.",
    "*→subnational_authority":     (
        "NOT portable as written. Kenya=county, Tanzania=region/district. "
        "Target the ROLE (subnational authority), never the Kenyan noun."
    ),
    "livestock/pastoralist cascades": (
        "Country-specific. Absent in Kenya's table, load-bearing in Tanzania's. "
        "Expect country #3 to surface a cascade class neither predecessor needed."
    ),
}


def tanzania_rules(include_cross_border: bool = True) -> list[RoutingRule]:
    """Tanzania's routing rules, optionally including KE–TZ cross-border cascades."""
    rules = TANZANIA_ROUTING_TABLE[:]
    if include_cross_border:
        rules += CROSS_BORDER_TABLE
    return rules

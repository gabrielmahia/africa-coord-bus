"""africa-coord-bus — Coordination event bus for East Africa MCP infrastructure."""
__version__ = "0.1.0"

from .event import CoordinationEvent, EventSeverity, EventDomain, KenyaLocation, SubnationalLocation
from .bus import EventBus
from .routing import RoutingRules, KENYA_ROUTING_TABLE, RoutingRule
from .domains import DomainCascade

__all__ = [
    "TANZANIA_ROUTING_TABLE",
    "CROSS_BORDER_TABLE",
    "PORTABLE_PATTERNS",
    "tanzania_rules",
    "CoordinationEvent", "EventSeverity", "EventDomain", "KenyaLocation", "SubnationalLocation",
    "EventBus", "RoutingRules", "KENYA_ROUTING_TABLE", "RoutingRule", "DomainCascade",
]

from .tanzania import (  # noqa: E402
    TANZANIA_ROUTING_TABLE,
    CROSS_BORDER_TABLE,
    PORTABLE_PATTERNS,
    tanzania_rules,
)

"""africa-coord-bus — Coordination event bus for East Africa MCP infrastructure."""
__version__ = "0.1.0"

from .event import CoordinationEvent, EventSeverity, EventDomain, KenyaLocation
from .bus import EventBus
from .routing import RoutingRules, KENYA_ROUTING_TABLE, RoutingRule
from .domains import DomainCascade

__all__ = [
    "CoordinationEvent", "EventSeverity", "EventDomain", "KenyaLocation",
    "EventBus", "RoutingRules", "KENYA_ROUTING_TABLE", "RoutingRule", "DomainCascade",
]

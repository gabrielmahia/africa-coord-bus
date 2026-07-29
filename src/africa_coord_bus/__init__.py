"""africa-coord-bus — Coordination event bus for East Africa MCP infrastructure."""
__version__ = "0.2.0"

from .event import CoordinationEvent, EventSeverity, EventDomain, KenyaLocation, SubnationalLocation
from .bus import EventBus
from .routing import RoutingRules, KENYA_ROUTING_TABLE, RoutingRule
from .domains import DomainCascade
from .cap import to_cap_xml, to_cap_dict
from .interop import to_hxl_row, hxl_header, ipc_severity_hint
from .queue import merge_queues, read_queue, write_queue, dedupe

__all__ = [
    "TANZANIA_ROUTING_TABLE",
    "CROSS_BORDER_TABLE",
    "PORTABLE_PATTERNS",
    "tanzania_rules",
    "CoordinationEvent", "EventSeverity", "EventDomain", "KenyaLocation", "SubnationalLocation",
    "EventBus", "RoutingRules", "KENYA_ROUTING_TABLE", "RoutingRule", "DomainCascade",
    "to_cap_xml", "to_cap_dict",
    "to_hxl_row", "hxl_header", "ipc_severity_hint",
    "merge_queues", "read_queue", "write_queue", "dedupe",
]

from .tanzania import (  # noqa: E402
    TANZANIA_ROUTING_TABLE,
    CROSS_BORDER_TABLE,
    PORTABLE_PATTERNS,
    tanzania_rules,
)

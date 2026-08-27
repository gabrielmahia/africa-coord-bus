"""africa-coord-bus — Coordination event bus for East Africa MCP infrastructure."""
__version__ = "0.4.0"

from .bus import EventBus
from .cap import to_cap_dict, to_cap_xml
from .domains import DomainCascade
from .event import (
    CoordinationEvent,
    EventConfidence,
    EventDomain,
    EventReality,
    EventSeverity,
    KenyaLocation,
    SubnationalLocation,
)
from .interop import hxl_header, ipc_severity_hint, to_hxl_row
from .queue import dedupe, merge_queues, read_queue, write_queue
from .routing import KENYA_ROUTING_TABLE, RoutingRule, RoutingRules

__all__ = [
    "CROSS_BORDER_TABLE",
    "KENYA_ROUTING_TABLE",
    "PORTABLE_PATTERNS",
    "TANZANIA_ROUTING_TABLE",
    "CoordinationEvent",
    "DomainCascade",
    "EventBus",
    "EventConfidence",
    "EventDomain",
    "EventReality",
    "EventSeverity",
    "KenyaLocation",
    "RoutingRule",
    "RoutingRules",
    "SubnationalLocation",
    "dedupe",
    "hxl_header",
    "ipc_severity_hint",
    "merge_queues",
    "read_queue",
    "tanzania_rules",
    "to_cap_dict",
    "to_cap_xml",
    "to_hxl_row",
    "write_queue",
]

from .tanzania import (
    CROSS_BORDER_TABLE,
    PORTABLE_PATTERNS,
    TANZANIA_ROUTING_TABLE,
    tanzania_rules,
)

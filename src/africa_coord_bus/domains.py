"""
DomainCascade — pre-wired coordination cascades for Kenya domains.

Each cascade knows which signals it cares about and what it does with them.
Domain implementers can swap in real MCP client calls.
"""
from __future__ import annotations

from typing import Callable

from .event import CoordinationEvent, EventDomain, EventSeverity
from .bus import EventBus


class DomainCascade:
    """
    Pre-wired cascade handlers for all Kenya coordination domains.

    By default uses log/print handlers (safe for testing and offline use).
    Replace with real MCP client callbacks for production.

    Usage:
        bus = EventBus()
        cascade = DomainCascade(bus)
        cascade.wire_all()

        # Now any drought event will cascade to agriculture + health + finance
    """

    def __init__(
        self,
        bus: EventBus,
        action_handler: Callable[[str, CoordinationEvent], None] | None = None,
    ):
        self.bus = bus
        # Default: print action to stdout (safe, observable, no side effects)
        self._act = action_handler or self._default_handler

    @staticmethod
    def _default_handler(action: str, event: CoordinationEvent) -> None:
        county = event.location.county or "unknown county"
        print(f"  [{event.domain.value.upper()}→{action.split('.')[0].upper()}] "
              f"{action} | {county} | {event.event_type} | {event.severity.value}")

    def wire_all(self) -> None:
        """Wire all domain cascade handlers."""
        self.wire_water()
        self.wire_agriculture()
        self.wire_health()
        self.wire_finance()
        self.wire_civic()

    def wire_water(self) -> None:
        """Water domain: drought + flood handling."""
        @self.bus.subscribe(EventDomain.WATER)
        def handle_water(event: CoordinationEvent, targets: list[str]) -> None:
            for t in targets:
                self._act(t, event)

    def wire_agriculture(self) -> None:
        """Agriculture domain: crop advisory + market alerts."""
        @self.bus.subscribe(EventDomain.AGRICULTURE)
        def handle_agriculture(event: CoordinationEvent, targets: list[str]) -> None:
            for t in targets:
                self._act(t, event)

    def wire_health(self) -> None:
        """Health domain: malnutrition + disease surveillance."""
        @self.bus.subscribe(EventDomain.HEALTH)
        def handle_health(event: CoordinationEvent, targets: list[str]) -> None:
            for t in targets:
                self._act(t, event)

    def wire_finance(self) -> None:
        """Finance domain: parametric insurance triggers."""
        @self.bus.subscribe(EventDomain.FINANCE)
        def handle_finance(event: CoordinationEvent, targets: list[str]) -> None:
            for t in targets:
                self._act(t, event)

    def wire_civic(self) -> None:
        """Civic domain: county alerts + procurement."""
        @self.bus.subscribe(EventDomain.CIVIC)
        def handle_civic(event: CoordinationEvent, targets: list[str]) -> None:
            for t in targets:
                self._act(t, event)

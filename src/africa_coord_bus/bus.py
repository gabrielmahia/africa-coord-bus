"""
EventBus — publish/subscribe coordination bus.

Offline-first: events are written to a local queue (JSONL file)
before being dispatched to subscribers. If dispatch fails,
events remain queued for replay.

Design principles:
  - Works with zero internet connectivity
  - Events never lost (append-only queue)
  - Subscribers are simple Python callables
  - Integration with MCP servers via HTTP handlers
"""
from __future__ import annotations

import json
import pathlib
import threading
from collections import defaultdict
from collections.abc import Callable

from .event import CoordinationEvent, EventDomain
from .routing import RoutingRules

HandlerFn = Callable[[CoordinationEvent, list[str]], None]


class EventBus:
    """
    Coordination event bus with offline-first queue and routing.

    Usage:
        bus = EventBus(queue_path="/var/coord-bus/queue.jsonl")

        # Subscribe a handler for agriculture events
        @bus.subscribe(EventDomain.AGRICULTURE)
        def handle_crop_advisory(event, targets):
            for t in targets:
                print(f"  → {t}: {event.location.country or 'KE'}/{event.location.admin_1}")

        # Publish a drought event from wapimaji-mcp
        bus.publish(CoordinationEvent(
            domain=EventDomain.WATER,
            event_type="drought_alert",
            source="wapimaji-mcp",
            severity=EventSeverity.ALERT,
            location=KenyaLocation(county="Turkana", county_code=23),
            data={"ndvi_anomaly": -0.28, "spi_3month": -1.8},
        ))
    """

    def __init__(
        self,
        queue_path: str | pathlib.Path | None = None,
        routing_rules: RoutingRules | None = None,
        auto_replay: bool = True,
    ):
        self._queue_path = pathlib.Path(queue_path) if queue_path else None
        self._routing = routing_rules or RoutingRules()
        self._subscribers: dict[str, list[HandlerFn]] = defaultdict(list)
        self._global_handlers: list[HandlerFn] = []
        self._lock = threading.Lock()
        self.published: list[CoordinationEvent] = []   # in-memory for testing
        self.dispatched: list[tuple[CoordinationEvent, list[str]]] = []

        if self._queue_path:
            self._queue_path.parent.mkdir(parents=True, exist_ok=True)

    # ── Subscription API ───────────────────────────────────────

    def subscribe(self, domain: EventDomain | None = None):
        """Decorator to subscribe a handler to events from a domain (or all)."""
        def decorator(fn: HandlerFn) -> HandlerFn:
            if domain is None:
                self._global_handlers.append(fn)
            else:
                key = domain.value if isinstance(domain, EventDomain) else domain
                self._subscribers[key].append(fn)
            return fn
        return decorator

    def add_handler(self, domain: EventDomain | None, fn: HandlerFn) -> None:
        """Programmatically add a handler."""
        if domain is None:
            self._global_handlers.append(fn)
        else:
            key = domain.value if isinstance(domain, EventDomain) else domain
            self._subscribers[key].append(fn)

    # ── Publish API ────────────────────────────────────────────

    def publish(self, event: CoordinationEvent) -> list[str]:
        """
        Publish an event to the bus.

        1. Writes to offline queue (if configured)
        2. Evaluates routing rules
        3. Dispatches to domain subscribers
        4. Returns list of target actions triggered

        Thread-safe. Never raises — failures are logged to queue.
        """
        with self._lock:
            # 1. Persist to queue
            if self._queue_path:
                with open(self._queue_path, "a") as f:
                    f.write(json.dumps({**event.to_dict(), "_queued": True}) + "\n")

            # 2. Evaluate routing
            targets = self._routing.get_targets(event)

            # 3. Dispatch to subscribers
            domain_key = event.domain.value if isinstance(event.domain, EventDomain) else event.domain
            handlers = self._subscribers.get(domain_key, []) + self._global_handlers

            for handler in handlers:
                try:
                    handler(event, targets)
                except Exception as e:
                    # Never let a handler crash the bus
                    if self._queue_path:
                        with open(self._queue_path, "a") as f:
                            f.write(json.dumps({
                                "error": str(e),
                                "event_id": event.event_id,
                                "handler": str(handler),
                            }) + "\n")

            self.published.append(event)
            self.dispatched.append((event, targets))
            return targets

    def replay_queue(self, since_event_id: str | None = None) -> int:
        """Replay events from the offline queue. Returns count replayed."""
        if not self._queue_path or not self._queue_path.exists():
            return 0
        count = 0
        found_start = since_event_id is None
        with open(self._queue_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                    if "error" in d:
                        continue
                    if not found_start:
                        if d.get("event_id") == since_event_id:
                            found_start = True
                        continue
                    event = CoordinationEvent.from_dict(d)
                    self.publish(event)
                    count += 1
                except Exception:
                    continue
        return count

    def stats(self) -> dict:
        """Return bus statistics."""
        queue_size = 0
        if self._queue_path and self._queue_path.exists():
            with open(self._queue_path) as f:
                queue_size = sum(1 for line in f if line.strip() and "error" not in line)
        return {
            "published_this_session": len(self.published),
            "dispatched_this_session": len(self.dispatched),
            "queue_file": str(self._queue_path) if self._queue_path else None,
            "queue_size": queue_size,
            "routing_rules": len(self._routing.rules),
            "domain_subscribers": {k: len(v) for k, v in self._subscribers.items()},
        }

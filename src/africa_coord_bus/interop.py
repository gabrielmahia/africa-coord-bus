"""Humanitarian interop — HXL tagging and an honesty-guarded IPC severity hint.

Two small, additive helpers that make coordination events legible to the
humanitarian-data ecosystem, alongside the CAP exporter (cap.py):

  - ``to_hxl_row`` / ``hxl_header``: tag event fields with HXL hashtags (the
    Humanitarian Exchange Language standard). An HXL-tagged table drops straight
    into HXL Proxy, HDX Quick Charts, and other humanitarian tooling with no
    manual column mapping.
  - ``ipc_severity_hint``: a COARSE mapping from event severity to an IPC-like
    phase, for food-security-relevant domains only. This is a legibility hint,
    NOT an IPC classification — see the strong caveat below.
"""
from __future__ import annotations

from .event import CoordinationEvent, EventDomain, EventSeverity

# Valid HXL core hashtags + attributes (hxlstandard.org).
_HXL_TAGS = {
    "meta_id": "#meta+id",
    "country": "#country+code",
    "adm1": "#adm1+name",
    "adm2": "#adm2+name",
    "lat": "#geo+lat",
    "lon": "#geo+lon",
    "date": "#date+occurred",
    "event": "#event+type",
    "severity": "#severity+type",
    "sector": "#sector+name",
    "org": "#org+name",
}


def hxl_header() -> dict[str, str]:
    """The HXL hashtag row (maps human column name -> HXL hashtag)."""
    return dict(_HXL_TAGS)


def to_hxl_row(event: CoordinationEvent) -> dict[str, str]:
    """One HXL-tagged row for the event: {hxl_hashtag: value}."""
    loc = event.location
    dom = event.domain.value if isinstance(event.domain, EventDomain) else event.domain
    sev = event.severity.value if isinstance(event.severity, EventSeverity) else event.severity
    raw = {
        "meta_id": event.event_id,
        "country": getattr(loc, "country", "") or "",
        "adm1": getattr(loc, "admin_1", "") or "",
        "adm2": getattr(loc, "admin_2", "") or "",
        "lat": getattr(loc, "lat", 0.0) or "",
        "lon": getattr(loc, "lon", 0.0) or "",
        "date": event.timestamp,
        "event": event.event_type,
        "severity": sev,
        "sector": dom,
        "org": event.source,
    }
    return {_HXL_TAGS[k]: str(v) for k, v in raw.items() if v != ""}


# --- IPC hint -----------------------------------------------------------------
# Food-security-relevant domains only. IPC phases 1..4 mapped from severity;
# phase 5 (Famine) is NEVER produced heuristically — famine is a formal
# analytical declaration, not something a severity map may assert.
_IPC_DOMAINS = {EventDomain.WATER, EventDomain.AGRICULTURE, EventDomain.HEALTH}
_IPC_FROM_SEVERITY = {
    EventSeverity.INFO:     (1, "Minimal"),
    EventSeverity.WARNING:  (2, "Stressed"),
    EventSeverity.ALERT:    (3, "Crisis"),
    EventSeverity.CRITICAL: (4, "Emergency"),
}
_IPC_CAVEAT = (
    "coarse severity->phase mapping for legibility only; NOT an IPC "
    "classification (IPC requires convergence-of-evidence analysis). "
    "Phase 5 (Famine) is never assigned heuristically."
)


def ipc_severity_hint(event: CoordinationEvent) -> dict | None:
    """A hard-labeled IPC phase *hint* for food-security-relevant events, else None.

    The caveat travels *inside* the returned dict on purpose (poka-yoke): the
    disclaimer cannot be dropped while keeping the number.
    """
    dom = event.domain if isinstance(event.domain, EventDomain) else EventDomain(event.domain)
    if dom not in _IPC_DOMAINS:
        return None
    sev = event.severity if isinstance(event.severity, EventSeverity) else EventSeverity(event.severity)
    phase, name = _IPC_FROM_SEVERITY[sev]
    return {"ipc_phase_hint": phase, "ipc_phase_name": name, "basis": _IPC_CAVEAT}

"""CAP 1.2 export — make coordination events legible to the emergency-response world.

The bus speaks its own schema internally. This module translates a
``CoordinationEvent`` into the OASIS **Common Alerting Protocol (CAP) 1.2** —
the standard consumed by national disaster agencies, Google Public Alerts,
IPAWS-style systems, and cross-border warning networks. The point is
interoperability without capture: a county or ministry can ingest a drought
alert as standards-compliant CAP *without adopting this bus*.

Design:
  - Purely additive. No change to CoordinationEvent or the wire format.
  - ``to_cap_dict`` for programmatic use; ``to_cap_xml`` for the wire.
  - DEMO/REAL discipline is preserved into CAP: a synthetic/demo event never
    emits as ``status=Actual``. It downgrades to ``Exercise`` so a test signal
    can never be mistaken for a live public alert.

Mappings are conservative and documented inline; CAP's controlled vocabularies
are respected exactly (invalid enum values would make the alert unparseable to
conformant consumers).
"""
from __future__ import annotations

from xml.etree import ElementTree as ET

from .event import (
    CoordinationEvent, EventDomain, EventSeverity, EventReality, EventConfidence,
)

# EventConfidence -> CAP <certainty> (Observed|Likely|Possible|Unlikely|Unknown)
_CERTAINTY = {
    EventConfidence.CONFIRMED: "Observed",
    EventConfidence.PROBABLE: "Likely",
    EventConfidence.SPECULATIVE: "Possible",
    EventConfidence.UNKNOWN: "Unknown",
}

CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"

# EventSeverity -> CAP <severity> (Extreme|Severe|Moderate|Minor|Unknown)
_SEVERITY = {
    EventSeverity.CRITICAL: "Extreme",
    EventSeverity.ALERT: "Severe",
    EventSeverity.WARNING: "Moderate",
    EventSeverity.INFO: "Minor",
}
# EventSeverity -> CAP <urgency> (Immediate|Expected|Future|Past|Unknown)
_URGENCY = {
    EventSeverity.CRITICAL: "Immediate",
    EventSeverity.ALERT: "Expected",
    EventSeverity.WARNING: "Future",
    EventSeverity.INFO: "Past",
}
# EventDomain -> CAP <category> (Geo|Met|Safety|Security|Rescue|Fire|Health|Env|
#                                Transport|Infra|CBRNE|Other)
_CATEGORY = {
    EventDomain.WATER: "Met",         # drought/flood are meteorological/hydrological
    EventDomain.HEALTH: "Health",
    EventDomain.AGRICULTURE: "Env",   # food-security / crop conditions
    EventDomain.ENERGY: "Infra",
    EventDomain.TRANSPORT: "Transport",
    EventDomain.EDUCATION: "Other",
    EventDomain.PROCUREMENT: "Other",
    EventDomain.FINANCE: "Other",
    EventDomain.CIVIC: "Safety",
}


def _is_demo(event: CoordinationEvent) -> bool:
    """True if the event is synthetic/demo, per the stack's labeling convention.

    Honours the ``"source": "DEMO — ..."`` convention and any ``demo``/
    ``synthetic`` flag in ``data``, plus a demo marker in the top-level source.
    """
    # Primary: the declared provenance field (reliable, not string-sniffed).
    r = getattr(event, "reality", EventReality.REAL)
    if (r.value if isinstance(r, EventReality) else r) == "demo":
        return True
    # Fallbacks for events produced before provenance was declared.
    src = (event.data.get("source") or "") if isinstance(event.data, dict) else ""
    if isinstance(src, str) and src.strip().upper().startswith("DEMO"):
        return True
    if isinstance(event.data, dict) and (event.data.get("demo") or event.data.get("synthetic")):
        return True
    return "demo" in (event.source or "").lower()


def _status(event: CoordinationEvent) -> str:
    # Trust integrity: synthetic data must never surface as a live public alert.
    return "Exercise" if _is_demo(event) else "Actual"


def _scope(event: CoordinationEvent) -> str:
    # aggregate/public -> Public; anything more sensitive -> Restricted.
    return "Public" if (event.privacy_level or "aggregate") in ("aggregate", "public") else "Restricted"


def _sev(event: CoordinationEvent) -> EventSeverity:
    return event.severity if isinstance(event.severity, EventSeverity) else EventSeverity(event.severity)


def _headline(event: CoordinationEvent) -> str:
    dom = event.domain.value if isinstance(event.domain, EventDomain) else event.domain
    return f"{_sev(event).value.title()}: {event.event_type} ({dom})"


def to_cap_dict(event: CoordinationEvent) -> dict:
    """Structured CAP 1.2 view of the event (dict form, for programmatic use)."""
    sev = _sev(event)
    dom = event.domain if isinstance(event.domain, EventDomain) else EventDomain(event.domain)
    loc = event.location
    area_desc = ", ".join(p for p in (getattr(loc, "admin_2", ""),
                                      getattr(loc, "admin_1", ""),
                                      getattr(loc, "country", "")) if p) or "Unspecified"
    return {
        "identifier": event.event_id,
        "sender": event.source,
        "sent": event.timestamp,
        "status": _status(event),
        "msgType": "Alert",
        "scope": _scope(event),
        "info": {
            "category": _CATEGORY.get(dom, "Other"),
            "event": event.event_type,
            "urgency": _URGENCY[sev],
            "severity": _SEVERITY[sev],
            "certainty": _CERTAINTY.get(
                event.confidence if isinstance(event.confidence, EventConfidence)
                else EventConfidence(event.confidence), "Unknown"),
            "senderName": event.source,
            "headline": _headline(event),
            "responseType": "Prepare" if event.requires_action else "Monitor",
            "area": {
                "areaDesc": area_desc,
                "lat": getattr(loc, "lat", 0.0),
                "lon": getattr(loc, "lon", 0.0),
            },
            # our custom fields survive as CAP <parameter>s rather than being lost
            "parameters": {
                **({k: v for k, v in event.data.items()} if isinstance(event.data, dict) else {}),
                "domain": dom.value,
                "cross_domain_refs": ",".join(event.cross_domain_refs),
                "privacy_level": event.privacy_level,
            },
        },
    }


def to_cap_xml(event: CoordinationEvent) -> str:
    """CAP 1.2 XML string for the event. Valid against the OASIS CAP 1.2 vocabulary."""
    d = to_cap_dict(event)
    alert = ET.Element("alert", xmlns=CAP_NS)
    for tag in ("identifier", "sender", "sent", "status", "msgType", "scope"):
        ET.SubElement(alert, tag).text = str(d[tag])
    info = ET.SubElement(alert, "info")
    i = d["info"]
    for tag in ("category", "event", "urgency", "severity", "certainty",
                "senderName", "headline", "responseType"):
        ET.SubElement(info, tag).text = str(i[tag])
    for name, value in i["parameters"].items():
        if value in (None, "", []):
            continue
        p = ET.SubElement(info, "parameter")
        ET.SubElement(p, "valueName").text = str(name)
        ET.SubElement(p, "value").text = str(value)
    area = ET.SubElement(info, "area")
    ET.SubElement(area, "areaDesc").text = i["area"]["areaDesc"]
    lat, lon = i["area"]["lat"], i["area"]["lon"]
    if lat or lon:
        # CAP circle: "lat,lon radiusKm"; radius 0 = a point
        ET.SubElement(area, "circle").text = f"{lat},{lon} 0"
    return ET.tostring(alert, encoding="unicode")

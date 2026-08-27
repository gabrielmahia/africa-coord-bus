"""Provenance fields — trust integrity made structural (declared, not sniffed)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from africa_coord_bus import (
    CoordinationEvent,
    EventConfidence,
    EventDomain,
    EventReality,
    EventSeverity,
    to_cap_dict,
    to_cap_xml,
)


def _ev(**kw):
    base = dict(domain=EventDomain.WATER, event_type="drought_alert",
                source="wapimaji-mcp", severity=EventSeverity.ALERT)
    base.update(kw)
    return CoordinationEvent(**base)


def test_defaults_are_real_and_unknown():
    e = _ev()
    assert e.reality == EventReality.REAL          # live systems default REAL
    assert e.confidence == EventConfidence.UNKNOWN  # undeclared confidence is unknown


def test_declared_demo_exports_as_exercise_without_any_demo_string():
    # the hole we closed: reality is declared, not sniffed from data["source"]
    e = _ev(reality=EventReality.DEMO, data={"spi_3month": -2.0})  # no "DEMO" text anywhere
    assert to_cap_dict(e)["status"] == "Exercise"
    assert "<status>Exercise</status>" in to_cap_xml(e)


def test_real_event_stays_actual():
    assert to_cap_dict(_ev())["status"] == "Actual"


def test_confidence_maps_to_cap_certainty():
    assert to_cap_dict(_ev(confidence=EventConfidence.CONFIRMED))["info"]["certainty"] == "Observed"
    assert to_cap_dict(_ev(confidence=EventConfidence.PROBABLE))["info"]["certainty"] == "Likely"
    assert to_cap_dict(_ev(confidence=EventConfidence.SPECULATIVE))["info"]["certainty"] == "Possible"
    assert to_cap_dict(_ev(confidence=EventConfidence.UNKNOWN))["info"]["certainty"] == "Unknown"


def test_roundtrip_preserves_provenance():
    e = _ev(reality=EventReality.DEMO, confidence=EventConfidence.PROBABLE, basis="modeled")
    e2 = CoordinationEvent.from_dict(e.to_dict())
    assert e2.reality == EventReality.DEMO
    assert e2.confidence == EventConfidence.PROBABLE
    assert e2.basis == "modeled"


def test_legacy_record_without_provenance_defaults_safely():
    # a pre-provenance queue record must not crash and must not become DEMO
    e = CoordinationEvent.from_dict({"domain": "water", "event_type": "x", "source": "s"})
    assert e.reality == EventReality.REAL
    assert e.confidence == EventConfidence.UNKNOWN


def test_legacy_demo_string_convention_still_honored():
    # defense in depth: old "DEMO —" convention still downgrades even if reality unset
    e = _ev(data={"source": "DEMO — synthetic scenario"})
    assert to_cap_dict(e)["status"] == "Exercise"

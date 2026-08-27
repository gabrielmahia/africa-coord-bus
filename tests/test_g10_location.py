"""G10: type-level country lock-in is fixed, with zero regression.

Poka-yoke intent: consumers written against either vocabulary keep working
no matter which location type flows through the bus.
"""

import json

from africa_coord_bus import (
    CoordinationEvent,
    EventDomain,
    EventSeverity,
    KenyaLocation,
    SubnationalLocation,
)


def test_kenya_location_unchanged_roundtrip():
    e = CoordinationEvent(domain=EventDomain.WATER, event_type="drought_alert",
                          source="wapimaji-mcp",
                          location=KenyaLocation(county="Turkana", county_code=23),
                          severity=EventSeverity.ALERT)
    d = e.to_dict()
    assert d["location"] == {"county": "Turkana", "county_code": 23}  # legacy wire shape
    e2 = CoordinationEvent.from_dict(json.loads(json.dumps(d)))
    assert isinstance(e2.location, KenyaLocation)
    assert e2.location.county == "Turkana" and e2.location.county_code == 23


def test_tanzania_location_roundtrip():
    e = CoordinationEvent(domain=EventDomain.AGRICULTURE, event_type="livestock_stress",
                          source="tz-pilot",
                          location=SubnationalLocation.tanzania(region="Dodoma", district="Bahi"))
    d = e.to_dict()
    assert d["location"]["country"] == "TZ" and d["location"]["admin_1"] == "Dodoma"
    e2 = CoordinationEvent.from_dict(d)
    assert isinstance(e2.location, SubnationalLocation)
    assert e2.location.admin_2 == "Bahi"


def test_shared_accessors_both_directions():
    ke = KenyaLocation(county="Kisumu", county_code=42, sub_county="Nyando")
    tz = SubnationalLocation.tanzania(region="Singida", district="Ikungi")
    # forward accessors on Kenya type
    assert ke.country == "KE" and ke.admin_1 == "Kisumu" and ke.admin_2 == "Nyando"
    # legacy accessors on neutral type
    assert tz.county == "Singida" and tz.sub_county == "Ikungi" and tz.county_code == 0
    # conversion preserves everything
    s = ke.to_subnational()
    assert (s.country, s.admin_1, s.admin_1_code, s.admin_2) == ("KE", "Kisumu", 42, "Nyando")


def test_legacy_and_empty_dicts_stay_kenya_typed():
    legacy = CoordinationEvent.from_dict({"domain": "water", "event_type": "x",
                                          "location": {"county": "Marsabit"}})
    assert isinstance(legacy.location, KenyaLocation)
    empty = CoordinationEvent.from_dict({"domain": "water", "event_type": "x"})
    assert isinstance(empty.location, KenyaLocation)


def test_default_construction_unchanged():
    e = CoordinationEvent(domain=EventDomain.HEALTH, event_type="t", source="s")
    assert isinstance(e.location, KenyaLocation)

"""CAP 1.2 export tests — mapping correctness + trust-integrity (DEMO never Actual)."""
import sys
import pathlib
from xml.etree import ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from africa_coord_bus import (
    CoordinationEvent, EventDomain, EventSeverity, KenyaLocation, SubnationalLocation,
    to_cap_xml, to_cap_dict,
)

CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"


def _drought(**kw):
    base = dict(
        domain=EventDomain.WATER, event_type="drought_alert", source="wapimaji-mcp",
        severity=EventSeverity.ALERT,
        location=KenyaLocation(county="Turkana", county_code=23, lat=3.11, lon=35.6),
        data={"spi_3month": -1.8, "rainfall_deficit_pct": 42},
        cross_domain_refs=["agriculture.crop_advisory", "finance.parametric_insurance_eval"],
        requires_action=True,
    )
    base.update(kw)
    return CoordinationEvent(**base)


def test_cap_dict_maps_vocabularies():
    d = to_cap_dict(_drought())
    assert d["status"] == "Actual"
    assert d["msgType"] == "Alert"
    assert d["scope"] == "Public"
    i = d["info"]
    assert i["category"] == "Met"          # water -> Met
    assert i["severity"] == "Severe"       # ALERT -> Severe
    assert i["urgency"] == "Expected"      # ALERT -> Expected
    assert i["responseType"] == "Prepare"  # requires_action
    assert "Turkana" in i["area"]["areaDesc"]
    # custom fields preserved as parameters, not dropped
    assert i["parameters"]["spi_3month"] == -1.8
    assert i["parameters"]["domain"] == "water"


def test_cap_xml_is_wellformed_and_namespaced():
    xml = to_cap_xml(_drought())
    root = ET.fromstring(xml)                       # raises if malformed
    assert root.tag in ("alert", f"{{{CAP_NS}}}alert")
    text = xml
    assert "<severity>Severe</severity>" in text
    assert "<circle>3.11,35.6 0</circle>" in text   # point geometry from lat/lon
    # custom data survived into a CAP parameter
    assert "<valueName>spi_3month</valueName>" in text


def test_demo_event_never_emits_as_actual():
    # trust integrity: synthetic data downgrades to Exercise
    demo = _drought(data={"source": "DEMO — synthetic drought scenario", "spi_3month": -2.0})
    assert to_cap_dict(demo)["status"] == "Exercise"
    assert "<status>Exercise</status>" in to_cap_xml(demo)


def test_severity_and_category_edges():
    crit = _drought(severity=EventSeverity.CRITICAL, domain=EventDomain.HEALTH,
                    event_type="cholera_cluster")
    d = to_cap_dict(crit)
    assert d["info"]["severity"] == "Extreme"      # CRITICAL -> Extreme
    assert d["info"]["urgency"] == "Immediate"
    assert d["info"]["category"] == "Health"


def test_restricted_scope_for_non_aggregate_privacy():
    e = _drought(privacy_level="individual")
    assert to_cap_dict(e)["scope"] == "Restricted"


def test_subnational_location_exports_cleanly():
    e = _drought(location=SubnationalLocation(country="TZ", admin_1="Dodoma", lat=-6.17, lon=35.74))
    d = to_cap_dict(e)
    assert "Dodoma" in d["info"]["area"]["areaDesc"]
    assert "TZ" in d["info"]["area"]["areaDesc"]

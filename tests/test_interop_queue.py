"""Tests: CRDT queue merge (algebraic laws) + HXL export + honesty-guarded IPC hint."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))

from africa_coord_bus import (
    CoordinationEvent, EventDomain, EventSeverity, KenyaLocation, SubnationalLocation,
    merge_queues, read_queue, write_queue, dedupe,
    to_hxl_row, hxl_header, ipc_severity_hint,
)


def _ev(eid, ts, **kw):
    e = CoordinationEvent(domain=EventDomain.WATER, event_type="drought_alert",
                          source="wapimaji-mcp", severity=EventSeverity.ALERT, **kw)
    e.event_id = eid
    e.timestamp = ts
    return e.to_dict()


A = [_ev("e1", "2026-07-01T00:00:00"), _ev("e2", "2026-07-02T00:00:00")]
B = [_ev("e2", "2026-07-02T00:00:00"), _ev("e3", "2026-07-03T00:00:00")]
C = [_ev("e4", "2026-07-04T00:00:00")]


# --- CRDT G-Set laws ---
def test_merge_dedupes_by_event_id():
    merged = merge_queues(A, B)
    ids = [d["event_id"] for d in merged]
    assert ids == ["e1", "e2", "e3"]           # e2 appears once, sorted by timestamp

def test_merge_is_idempotent():
    assert merge_queues(A, A) == merge_queues(A)

def test_merge_is_commutative():
    assert merge_queues(A, B) == merge_queues(B, A)

def test_merge_is_associative():
    left = merge_queues(merge_queues(A, B), C)
    right = merge_queues(A, merge_queues(B, C))
    assert left == right

def test_merge_reads_jsonl_files(tmp_path):
    fa, fb = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    write_queue(A, fa); write_queue(B, fb)
    merged = merge_queues(fa, fb)
    assert [d["event_id"] for d in merged] == ["e1", "e2", "e3"]

def test_read_queue_skips_error_lines(tmp_path):
    f = tmp_path / "q.jsonl"
    f.write_text(
        '{"event_id":"e1","timestamp":"2026-07-01T00:00:00"}\n'
        '{"error":"handler blew up","event_id":"e1"}\n'   # diagnostic line, skipped
        '\n'
        '{"event_id":"e2","timestamp":"2026-07-02T00:00:00"}\n'
    )
    assert [d["event_id"] for d in read_queue(f)] == ["e1", "e2"]

def test_dedupe_keeps_one_per_id():
    assert len(dedupe(A + B)) == 3


# --- HXL export ---
def test_hxl_row_uses_valid_hashtags():
    e = CoordinationEvent(domain=EventDomain.WATER, event_type="drought_alert",
                          source="wapimaji-mcp", severity=EventSeverity.ALERT,
                          location=KenyaLocation(county="Turkana", county_code=23, lat=3.11, lon=35.6))
    row = to_hxl_row(e)
    assert row["#event+type"] == "drought_alert"
    assert row["#severity+type"] == "alert"
    assert row["#adm1+name"] == "Turkana"
    assert row["#geo+lat"] == "3.11"
    assert row["#sector+name"] == "water"
    assert set(to_hxl_row(e)).issubset(set(hxl_header().values()))

def test_hxl_row_omits_empty_fields():
    e = CoordinationEvent(domain=EventDomain.CIVIC, event_type="budget_published",
                          source="jumuia-mcp", location=SubnationalLocation(country="KE"))
    row = to_hxl_row(e)
    assert "#adm2+name" not in row        # no admin_2 -> omitted, not blank


# --- IPC hint honesty guards ---
def test_ipc_hint_maps_food_security_domains():
    e = CoordinationEvent(domain=EventDomain.AGRICULTURE, event_type="crop_failure",
                          source="shamba-ai", severity=EventSeverity.CRITICAL)
    h = ipc_severity_hint(e)
    assert h["ipc_phase_hint"] == 4 and h["ipc_phase_name"] == "Emergency"
    assert "NOT an IPC classification" in h["basis"]     # caveat travels with the number

def test_ipc_hint_never_returns_phase_5():
    for sev in EventSeverity:
        e = CoordinationEvent(domain=EventDomain.HEALTH, event_type="x", source="s", severity=sev)
        assert ipc_severity_hint(e)["ipc_phase_hint"] <= 4   # Famine is never heuristic

def test_ipc_hint_none_for_non_food_domains():
    e = CoordinationEvent(domain=EventDomain.TRANSPORT, event_type="road_closed", source="s",
                          severity=EventSeverity.CRITICAL)
    assert ipc_severity_hint(e) is None

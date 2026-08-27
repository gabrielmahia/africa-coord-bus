"""Offline-queue merge — a conflict-free (CRDT) union of append-only event logs.

The offline queue (see EventBus) is an append-only JSONL log of coordination
events. Events are **immutable** and each carries a unique ``event_id`` (uuid4).
That data model *is* a grow-only set (G-Set): the mathematically correct way to
reconcile two logs — two field devices, or a partially-synced replica — is
**union, deduplicated by event_id**.

Why this matters: ``EventBus.replay_queue`` has no dedup, so naively
concatenating two devices' queues (or replaying one twice) double-publishes the
same event. ``merge_queues`` gives the reconciliation the offline-first design
implied but never provided, with the CRDT guarantees that make offline sync safe:

  - **idempotent**  merge(A, A) == A            (replay-safe)
  - **commutative** merge(A, B) == merge(B, A)  (order of sync doesn't matter)
  - **associative** merge(merge(A,B),C) == merge(A,merge(B,C))

Because events are immutable, a G-Set is sufficient — there are no updates to a
given id to resolve, so no last-writer-wins register is needed. If events ever
become mutable, this must be revisited (an LWW-register or OR-Set per id).
"""
from __future__ import annotations

import json
import pathlib
from collections.abc import Iterable

_QueueSource = "str | pathlib.Path | Iterable[dict]"


def read_queue(source) -> list[dict]:
    """Read event records from a JSONL queue file (or pass through a list of dicts).

    Skips blank lines and error/diagnostic lines (those without an ``event_id``),
    so only real events are returned.
    """
    if isinstance(source, (str, pathlib.Path)):
        p = pathlib.Path(source)
        if not p.exists():
            return []
        records = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "event_id" in d and "error" not in d:
                    records.append(d)
        return records
    # already an iterable of dicts
    return [d for d in source if isinstance(d, dict) and d.get("event_id") and "error" not in d]


def dedupe(records: Iterable[dict]) -> list[dict]:
    """Collapse records to one per event_id (first occurrence wins — events are immutable)."""
    seen: dict[str, dict] = {}
    for d in records:
        eid = d.get("event_id")
        if eid and eid not in seen:
            seen[eid] = d
    return list(seen.values())


def _sort_key(d: dict):
    # deterministic, replica-independent ordering: timestamp then event_id
    return (d.get("timestamp", ""), d.get("event_id", ""))


def merge_queues(*sources) -> list[dict]:
    """Conflict-free union of one or more queues (files or lists of dicts).

    Deduplicates by ``event_id`` and returns a deterministically ordered list
    (by timestamp, then event_id) so every replica computes the identical merged
    log regardless of sync order. This is the G-Set merge: idempotent,
    commutative, associative.
    """
    all_records: list[dict] = []
    for s in sources:
        all_records.extend(read_queue(s))
    return sorted(dedupe(all_records), key=_sort_key)


def write_queue(records: Iterable[dict], path) -> int:
    """Write records to a JSONL queue file. Returns the number written."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(p, "w") as f:
        for d in records:
            f.write(json.dumps(d) + "\n")
            n += 1
    return n

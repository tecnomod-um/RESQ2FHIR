from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Iterable


def _bundle_kind(path: Path, bundle: dict) -> str:
    """Classify a Bundle without relying only on its filename."""
    name = path.name
    if name.endswith(".document.json") or bundle.get("type") == "document":
        return "document"
    if name.endswith(".transaction.json") or bundle.get("type") == "transaction":
        return "transaction"
    return str(bundle.get("type") or "other")


def summarize_resource_counts(bundle_paths: Iterable[Path]) -> dict:
    """Return aggregate Bundle/resource counts without exposing patient data.

    Counts are separated by Bundle type so document Bundles do not inflate the
    transaction-resource statistics used in the manuscript evaluation.
    """
    by_kind: dict[str, Counter] = {}
    bundle_counts: Counter = Counter()
    total_entries: Counter = Counter()
    unreadable = 0

    for path in bundle_paths:
        path = Path(path)
        try:
            bundle = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            unreadable += 1
            continue

        kind = _bundle_kind(path, bundle)
        bundle_counts[kind] += 1
        counter = by_kind.setdefault(kind, Counter())

        for entry in bundle.get("entry") or []:
            resource = entry.get("resource") if isinstance(entry, dict) else None
            if not isinstance(resource, dict):
                continue
            resource_type = resource.get("resourceType")
            if not resource_type:
                continue
            counter[resource_type] += 1
            total_entries[kind] += 1

    tx_count = bundle_counts.get("transaction", 0)
    tx_resources = total_entries.get("transaction", 0)

    return {
        "bundleCounts": dict(sorted(bundle_counts.items())),
        "unreadableBundles": unreadable,
        "resourceCountsByBundleType": {
            kind: dict(sorted(counter.items()))
            for kind, counter in sorted(by_kind.items())
        },
        "totalResourcesByBundleType": dict(sorted(total_entries.items())),
        "transaction": {
            "bundles": tx_count,
            "resources": tx_resources,
            "meanResourcesPerBundle": (tx_resources / tx_count) if tx_count else None,
            "byResourceType": dict(sorted(by_kind.get("transaction", Counter()).items())),
        },
    }
